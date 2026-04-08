"""A2A server entry point for fertility-sense agents."""

from __future__ import annotations

from pathlib import Path

from fertility_sense.config import FertilitySenseConfig
from fertility_sense.nemoclaw.agents import ALL_AGENTS, AGENT_MAP, AgentConfig
from fertility_sense.nemoclaw.dispatcher import AgentDispatcher, DispatchResult
from fertility_sense.nemoclaw.orchestrator import FertilityOrchestrator
from fertility_sense.nemoclaw.router import route_to_agent


class FertilitySenseServer:
    """Server that exposes fertility-sense agents via A2A protocol.

    In production, this wraps the nemoclaw A2A server from nemo-fleet.
    This implementation provides the registration and routing skeleton.
    """

    def __init__(self, config: FertilitySenseConfig | None = None) -> None:
        self.config = config or FertilitySenseConfig()

        # Build Claude client if API key is available
        self._client = None
        if self.config.anthropic_api_key:
            try:
                from fertility_sense.nemoclaw.claude_client import ClaudeClient

                self._client = ClaudeClient(
                    api_key=self.config.anthropic_api_key,
                    budget_usd=self.config.cost_budget_usd,
                    rate_limit_rpm=self.config.rate_limit_rpm,
                )
            except ImportError:
                pass  # anthropic SDK not installed — run in offline mode

        # Build dispatcher (works with or without a client)
        agents_dir = self.config.base_dir / "agents"
        self.dispatcher = AgentDispatcher(
            client=self._client,
            agents_dir=agents_dir,
        )

        # Orchestrator wired to dispatcher
        self.orchestrator = FertilityOrchestrator(dispatcher=self.dispatcher)

        self._agents: dict[str, AgentConfig] = {}
        self._register_agents()

    def _register_agents(self) -> None:
        """Register all fertility-sense agents."""
        for agent in ALL_AGENTS:
            if agent.enabled:
                self._agents[agent.name] = agent

    def list_agents(self) -> list[AgentConfig]:
        """List all registered agents."""
        return list(self._agents.values())

    def get_agent(self, name: str) -> AgentConfig | None:
        """Get agent config by name."""
        return self._agents.get(name)

    def route(self, prompt: str, skill: str | None = None, agent: str | None = None) -> AgentConfig:
        """Route a request to the appropriate agent."""
        return route_to_agent(prompt, skill, agent)

    def handle_task(
        self,
        prompt: str,
        skill: str | None = None,
        agent: str | None = None,
    ) -> DispatchResult:
        """Handle a single task via A2A protocol.

        Routes the request to the appropriate agent and dispatches it.
        """
        target = self.route(prompt, skill=skill, agent=agent)
        return self.dispatcher.dispatch(
            agent_name=target.name,
            skill_name=skill,
            prompt=prompt,
        )

    def run_pipeline(self, run_id: str) -> dict:
        """Run the full intelligence pipeline."""
        result = self.orchestrator.execute_pipeline(run_id)
        return {
            "run_id": result.run_id,
            "status": result.status,
            "phases": [
                {
                    "phase": p.phase.value,
                    "status": p.status,
                    "agents": p.agents_run,
                }
                for p in result.phases
            ],
        }
