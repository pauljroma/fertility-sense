"""Unit tests for agent runtime."""

import pytest

from fertility_sense.nemoclaw.agents import (
    ALL_AGENTS,
    AGENT_MAP,
    AgentRole,
    ClaudeTier,
    ROLE_TIER_MAP,
)
from fertility_sense.nemoclaw.skills import ALL_SKILLS, SKILL_MAP
from fertility_sense.nemoclaw.router import route_to_agent


@pytest.mark.unit
def test_all_agents_registered():
    assert len(ALL_AGENTS) == 11
    names = {a.name for a in ALL_AGENTS}
    expected = {
        "demand-scout", "evidence-curator", "safety-sentinel",
        "ontology-keeper", "signal-ranker", "answer-assembler",
        "product-translator", "ops-monitor",
        "rfp-responder", "competitive-intel", "deal-manager",
    }
    assert names == expected


@pytest.mark.unit
def test_agent_roles():
    assert AGENT_MAP["demand-scout"].role == AgentRole.ANALYST
    assert AGENT_MAP["signal-ranker"].role == AgentRole.EXECUTOR
    assert AGENT_MAP["ontology-keeper"].role == AgentRole.PLANNER


@pytest.mark.unit
def test_agent_tiers():
    assert AGENT_MAP["demand-scout"].default_tier == ClaudeTier.SONNET
    assert AGENT_MAP["signal-ranker"].default_tier == ClaudeTier.HAIKU
    assert AGENT_MAP["ontology-keeper"].default_tier == ClaudeTier.OPUS


@pytest.mark.unit
def test_all_agents_have_skills():
    for agent in ALL_AGENTS:
        assert len(agent.skills) >= 3, f"{agent.name} has fewer than 3 skills"


@pytest.mark.unit
def test_all_skills_registered():
    assert len(ALL_SKILLS) >= 30  # 4+ skills per 8 agents


@pytest.mark.unit
def test_skill_map_consistency():
    for skill in ALL_SKILLS:
        assert skill.name in SKILL_MAP


@pytest.mark.unit
def test_router_explicit_agent():
    agent = route_to_agent("anything", agent="evidence-curator")
    assert agent.name == "evidence-curator"


@pytest.mark.unit
def test_router_keyword_fda():
    agent = route_to_agent("Check FDA alerts for this medication")
    assert agent.name == "safety-sentinel"


@pytest.mark.unit
def test_router_keyword_trend():
    agent = route_to_agent("What are the latest search trends?")
    assert agent.name == "demand-scout"


@pytest.mark.unit
def test_router_keyword_score():
    agent = route_to_agent("compute the tos and rank by demand")
    assert agent.name == "signal-ranker"


@pytest.mark.unit
def test_router_default():
    agent = route_to_agent("hello world")
    assert agent.name == "demand-scout"  # Default


@pytest.mark.unit
def test_orchestrator_pipeline():
    from fertility_sense.nemoclaw.orchestrator import FertilityOrchestrator

    orch = FertilityOrchestrator()
    result = orch.execute_pipeline("test-001")
    assert result.status == "completed"
    assert len(result.phases) == 4
