"""Tests for the agent runtime: ClaudeClient, AgentDispatcher, wired orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fertility_sense.nemoclaw.agents import AGENT_MAP, AgentConfig, ClaudeTier
from fertility_sense.nemoclaw.claude_client import (
    BudgetExceededError,
    ClaudeClient,
    RateLimitError,
    UsageRecord,
    _compute_cost,
)
from fertility_sense.nemoclaw.dispatcher import AgentDispatcher, DispatchResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_client(
    response_text: str = "mock response",
    input_tokens: int = 100,
    output_tokens: int = 50,
    budget_usd: float = 10.0,
) -> ClaudeClient:
    """Build a ClaudeClient whose underlying Anthropic client is mocked.

    Bypasses __init__ (which tries to import anthropic) and wires up
    internal state directly.
    """
    from collections import deque

    mock_sdk_client = MagicMock()

    # Construct the client without calling __init__
    client = ClaudeClient.__new__(ClaudeClient)
    client._client = mock_sdk_client
    client._budget_usd = budget_usd
    client._rate_limit_rpm = 60
    client._total_spend = 0.0
    client._usage_log = []
    client._call_times = deque()

    # Wire up the mock response
    mock_response = MagicMock()
    mock_response.usage.input_tokens = input_tokens
    mock_response.usage.output_tokens = output_tokens

    mock_block = MagicMock()
    mock_block.text = response_text
    mock_response.content = [mock_block]

    mock_sdk_client.messages.create.return_value = mock_response
    return client


# ---------------------------------------------------------------------------
# ClaudeClient cost computation
# ---------------------------------------------------------------------------

class TestCostComputation:
    @pytest.mark.unit
    def test_haiku_cost(self):
        cost = _compute_cost("claude-haiku-4-5-20251001", 1_000_000, 1_000_000)
        assert cost == pytest.approx(6.0)  # $1 input + $5 output

    @pytest.mark.unit
    def test_sonnet_cost(self):
        cost = _compute_cost("claude-sonnet-4-6-20250514", 1_000_000, 1_000_000)
        assert cost == pytest.approx(18.0)  # $3 input + $15 output

    @pytest.mark.unit
    def test_opus_cost(self):
        cost = _compute_cost("claude-opus-4-6-20250514", 1_000_000, 1_000_000)
        assert cost == pytest.approx(90.0)  # $15 input + $75 output

    @pytest.mark.unit
    def test_small_call(self):
        # 100 input tokens, 50 output tokens on Haiku
        cost = _compute_cost("claude-haiku-4-5-20251001", 100, 50)
        expected = (100 * 1.0 + 50 * 5.0) / 1_000_000
        assert cost == pytest.approx(expected)


# ---------------------------------------------------------------------------
# ClaudeClient tracking + budget
# ---------------------------------------------------------------------------

class TestClaudeClientTracking:
    @pytest.mark.unit
    def test_call_tracks_usage(self):
        client = _make_mock_client(response_text="hello", input_tokens=200, output_tokens=100)
        text, record = client.call(
            model="claude-haiku-4-5-20251001",
            system="system",
            prompt="test",
            agent="demand-scout",
            skill="trend-analysis",
        )
        assert text == "hello"
        assert record.agent == "demand-scout"
        assert record.skill == "trend-analysis"
        assert record.input_tokens == 200
        assert record.output_tokens == 100
        assert client.total_spend > 0
        assert len(client.usage_log) == 1

    @pytest.mark.unit
    def test_budget_enforcement(self):
        client = _make_mock_client(budget_usd=0.0)
        with pytest.raises(BudgetExceededError):
            client.call(
                model="claude-haiku-4-5-20251001",
                system="sys",
                prompt="test",
            )

    @pytest.mark.unit
    def test_budget_remaining(self):
        client = _make_mock_client(budget_usd=5.0)
        assert client.budget_remaining() == pytest.approx(5.0)
        # Make a call
        client.call(model="claude-haiku-4-5-20251001", system="s", prompt="p")
        assert client.budget_remaining() < 5.0

    @pytest.mark.unit
    def test_rate_limit_enforcement(self):
        client = _make_mock_client()
        client._rate_limit_rpm = 2
        # First two calls succeed
        client.call(model="claude-haiku-4-5-20251001", system="s", prompt="p")
        client.call(model="claude-haiku-4-5-20251001", system="s", prompt="p")
        # Third should be rate-limited
        with pytest.raises(RateLimitError):
            client.call(model="claude-haiku-4-5-20251001", system="s", prompt="p")


# ---------------------------------------------------------------------------
# AgentDispatcher — prompt loading
# ---------------------------------------------------------------------------

class TestDispatcherPromptLoading:
    @pytest.mark.unit
    def test_loads_system_prompt_from_agents_dir(self, tmp_path: Path):
        agent_dir = tmp_path / "agents"
        agent_dir.mkdir()
        (agent_dir / "demand-scout.md").write_text(
            "---\nname: demand-scout\n---\n\nYou are the demand-scout agent."
        )

        dispatcher = AgentDispatcher(client=None, agents_dir=agent_dir)
        prompt = dispatcher._load_system_prompt(AGENT_MAP["demand-scout"])
        assert "You are the demand-scout agent." in prompt
        # Frontmatter should be stripped
        assert "---" not in prompt

    @pytest.mark.unit
    def test_loads_from_real_agents_dir(self):
        agents_dir = Path("/Users/expo/fertility-sense/agents")
        if not agents_dir.exists():
            pytest.skip("agents/ directory not present")
        dispatcher = AgentDispatcher(client=None, agents_dir=agents_dir)
        prompt = dispatcher._load_system_prompt(AGENT_MAP["demand-scout"])
        assert "demand-scout" in prompt
        assert len(prompt) > 50

    @pytest.mark.unit
    def test_fallback_when_file_missing(self, tmp_path: Path):
        dispatcher = AgentDispatcher(client=None, agents_dir=tmp_path)
        prompt = dispatcher._load_system_prompt(AGENT_MAP["demand-scout"])
        assert "demand-scout" in prompt
        assert "Monitors" in prompt  # from AgentConfig.description

    @pytest.mark.unit
    def test_prompt_cache(self, tmp_path: Path):
        agent_dir = tmp_path / "agents"
        agent_dir.mkdir()
        (agent_dir / "demand-scout.md").write_text("---\nname: x\n---\n\nCached body.")
        dispatcher = AgentDispatcher(client=None, agents_dir=agent_dir)
        # Load twice
        p1 = dispatcher._load_system_prompt(AGENT_MAP["demand-scout"])
        p2 = dispatcher._load_system_prompt(AGENT_MAP["demand-scout"])
        assert p1 == p2
        assert p1 == "Cached body."


# ---------------------------------------------------------------------------
# AgentDispatcher — model resolution
# ---------------------------------------------------------------------------

class TestDispatcherModelResolution:
    @pytest.mark.unit
    def test_default_tier_for_agent(self):
        dispatcher = AgentDispatcher(client=None)
        model = dispatcher._resolve_model(AGENT_MAP["demand-scout"], None)
        assert model == ClaudeTier.SONNET.value

    @pytest.mark.unit
    def test_skill_tier_override(self):
        dispatcher = AgentDispatcher(client=None)
        # telemetry-parse has HAIKU override
        model = dispatcher._resolve_model(AGENT_MAP["demand-scout"], "telemetry-parse")
        assert model == ClaudeTier.HAIKU.value

    @pytest.mark.unit
    def test_skill_without_override_uses_default(self):
        dispatcher = AgentDispatcher(client=None)
        # trend-analysis has no override
        model = dispatcher._resolve_model(AGENT_MAP["demand-scout"], "trend-analysis")
        assert model == ClaudeTier.SONNET.value

    @pytest.mark.unit
    def test_executor_defaults_to_haiku(self):
        dispatcher = AgentDispatcher(client=None)
        model = dispatcher._resolve_model(AGENT_MAP["signal-ranker"], None)
        assert model == ClaudeTier.HAIKU.value

    @pytest.mark.unit
    def test_planner_defaults_to_opus(self):
        dispatcher = AgentDispatcher(client=None)
        model = dispatcher._resolve_model(AGENT_MAP["ontology-keeper"], None)
        assert model == ClaudeTier.OPUS.value


# ---------------------------------------------------------------------------
# AgentDispatcher — offline dispatch
# ---------------------------------------------------------------------------

class TestDispatcherOffline:
    @pytest.mark.unit
    def test_offline_returns_placeholder(self):
        dispatcher = AgentDispatcher(client=None)
        result = dispatcher.dispatch("demand-scout", prompt="analyze trends")
        assert result.status == "offline"
        assert "demand-scout" in result.output
        assert result.usage is None

    @pytest.mark.unit
    def test_unknown_agent_fails(self):
        dispatcher = AgentDispatcher(client=None)
        result = dispatcher.dispatch("nonexistent-agent", prompt="hello")
        assert result.status == "failed"
        assert "Unknown agent" in result.error

    @pytest.mark.unit
    def test_context_included_in_prompt(self):
        dispatcher = AgentDispatcher(client=None)
        result = dispatcher.dispatch(
            "demand-scout",
            prompt="analyze",
            context={"topic": "ivf-cost"},
        )
        assert result.status == "offline"
        # The offline output echoes the prompt (first 120 chars)
        assert "analyze" in result.output


# ---------------------------------------------------------------------------
# AgentDispatcher — live dispatch (mocked)
# ---------------------------------------------------------------------------

class TestDispatcherLive:
    @pytest.mark.unit
    def test_live_dispatch_returns_completed(self, tmp_path: Path):
        client = _make_mock_client(response_text="Agent output here")
        agent_dir = tmp_path
        (agent_dir / "demand-scout.md").write_text("---\nname: x\n---\n\nSystem prompt.")

        dispatcher = AgentDispatcher(client=client, agents_dir=agent_dir)
        result = dispatcher.dispatch("demand-scout", prompt="analyze trends")
        assert result.status == "completed"
        assert result.output == "Agent output here"
        assert result.usage is not None
        assert result.model_used == ClaudeTier.SONNET.value

    @pytest.mark.unit
    def test_budget_exceeded_returns_status(self, tmp_path: Path):
        client = _make_mock_client(budget_usd=0.0)
        dispatcher = AgentDispatcher(client=client, agents_dir=tmp_path)
        result = dispatcher.dispatch("demand-scout", prompt="analyze")
        assert result.status == "budget_exceeded"


# ---------------------------------------------------------------------------
# Orchestrator with dispatcher
# ---------------------------------------------------------------------------

class TestOrchestratorWithDispatcher:
    @pytest.mark.unit
    def test_pipeline_runs_all_4_phases_offline(self):
        dispatcher = AgentDispatcher(client=None)
        from fertility_sense.nemoclaw.orchestrator import FertilityOrchestrator

        orch = FertilityOrchestrator(dispatcher=dispatcher)
        run = orch.execute_pipeline("test-runtime-001")
        assert run.status == "completed"
        assert len(run.phases) == 4

        # Verify all agents were dispatched
        all_agents_run = []
        for phase in run.phases:
            all_agents_run.extend(phase.agents_run)
        assert "demand-scout" in all_agents_run
        assert "answer-assembler" in all_agents_run
        assert "product-translator" in all_agents_run

    @pytest.mark.unit
    def test_pipeline_without_dispatcher_still_works(self):
        """Backward compat: orchestrator without dispatcher uses stub."""
        from fertility_sense.nemoclaw.orchestrator import FertilityOrchestrator

        orch = FertilityOrchestrator()
        run = orch.execute_pipeline("test-compat-001")
        assert run.status == "completed"
        assert len(run.phases) == 4

    @pytest.mark.unit
    def test_single_phase_with_dispatcher(self):
        dispatcher = AgentDispatcher(client=None)
        from fertility_sense.nemoclaw.orchestrator import (
            FertilityOrchestrator,
            PipelinePhase,
        )

        orch = FertilityOrchestrator(dispatcher=dispatcher)
        result = orch.execute_phase("test-phase", PipelinePhase.INGEST)
        assert result.status == "completed"
        assert "demand-scout" in result.agents_run
        assert "evidence-curator" in result.agents_run
        assert "safety-sentinel" in result.agents_run

    @pytest.mark.unit
    def test_phase_outputs_contain_dispatch_info(self):
        dispatcher = AgentDispatcher(client=None)
        from fertility_sense.nemoclaw.orchestrator import (
            FertilityOrchestrator,
            PipelinePhase,
        )

        orch = FertilityOrchestrator(dispatcher=dispatcher)
        result = orch.execute_phase("test-outputs", PipelinePhase.SCORE)
        # With dispatcher, outputs should contain status/model keys
        for agent_name in result.agents_run:
            assert "status" in result.outputs[agent_name]
            assert "model" in result.outputs[agent_name]
