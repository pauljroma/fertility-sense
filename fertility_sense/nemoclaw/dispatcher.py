"""Agent dispatcher -- loads prompts, selects tier, calls Claude, returns results."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fertility_sense.nemoclaw.agents import AgentConfig, AGENT_MAP, ClaudeTier, ROLE_TIER_MAP
from fertility_sense.nemoclaw.claude_client import ClaudeClient, UsageRecord, BudgetExceededError


@dataclass
class DispatchResult:
    """Result from dispatching a task to an agent."""

    agent_name: str
    skill_name: str
    model_used: str
    output: str
    usage: UsageRecord | None
    status: str  # "completed", "failed", "budget_exceeded", "offline"
    error: str | None = None


# Regex to strip YAML frontmatter (--- ... ---)
_FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)


class AgentDispatcher:
    """Loads agent system prompts and dispatches tasks to Claude."""

    def __init__(
        self,
        client: ClaudeClient | None = None,
        agents_dir: Path | None = None,
    ) -> None:
        self._client = client
        self._agents_dir = agents_dir or Path("agents")
        # Cache: agent_name -> system prompt body (markdown without frontmatter)
        self._prompt_cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Prompt loading
    # ------------------------------------------------------------------

    def _load_system_prompt(self, agent: AgentConfig) -> str:
        """Read agents/{name}.md, strip YAML frontmatter, return markdown body."""
        if agent.name in self._prompt_cache:
            return self._prompt_cache[agent.name]

        prompt_path = self._agents_dir / f"{agent.name}.md"
        if not prompt_path.exists():
            fallback = f"You are the {agent.name} agent. {agent.description}"
            self._prompt_cache[agent.name] = fallback
            return fallback

        raw = prompt_path.read_text(encoding="utf-8")
        body = _FRONTMATTER_RE.sub("", raw).strip()
        self._prompt_cache[agent.name] = body
        return body

    # ------------------------------------------------------------------
    # Model resolution
    # ------------------------------------------------------------------

    def _resolve_model(self, agent: AgentConfig, skill_name: str | None) -> str:
        """Determine which Claude model to use.

        Priority:
        1. Skill-level tier override
        2. Agent default tier (role-based)
        """
        if skill_name:
            for skill in agent.skills:
                if skill.name == skill_name and skill.tier_override is not None:
                    return skill.tier_override.value
        return agent.default_tier.value

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def dispatch(
        self,
        agent_name: str,
        skill_name: str | None = None,
        prompt: str = "",
        context: dict[str, Any] | None = None,
    ) -> DispatchResult:
        """Dispatch a task to a specific agent (and optionally skill).

        If no ClaudeClient is available, returns a placeholder result (offline mode).
        """
        agent = AGENT_MAP.get(agent_name)
        if agent is None:
            return DispatchResult(
                agent_name=agent_name,
                skill_name=skill_name or "",
                model_used="",
                output="",
                usage=None,
                status="failed",
                error=f"Unknown agent: {agent_name}",
            )

        model = self._resolve_model(agent, skill_name)
        system_prompt = self._load_system_prompt(agent)

        # Build the full user prompt with optional context
        full_prompt = prompt
        if context:
            ctx_lines = [f"- {k}: {v}" for k, v in context.items()]
            full_prompt = "Context:\n" + "\n".join(ctx_lines) + "\n\n" + prompt

        # Offline mode — no client
        if self._client is None:
            return DispatchResult(
                agent_name=agent_name,
                skill_name=skill_name or "",
                model_used=model,
                output=f"[offline] Agent {agent_name} would process: {prompt[:120]}",
                usage=None,
                status="offline",
            )

        # Live mode — call Claude
        try:
            text, usage = self._client.call(
                model=model,
                system=system_prompt,
                prompt=full_prompt,
                max_tokens=agent.max_tokens,
                temperature=agent.temperature,
                agent=agent_name,
                skill=skill_name or "",
            )
            return DispatchResult(
                agent_name=agent_name,
                skill_name=skill_name or "",
                model_used=model,
                output=text,
                usage=usage,
                status="completed",
            )
        except BudgetExceededError as exc:
            return DispatchResult(
                agent_name=agent_name,
                skill_name=skill_name or "",
                model_used=model,
                output="",
                usage=None,
                status="budget_exceeded",
                error=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            return DispatchResult(
                agent_name=agent_name,
                skill_name=skill_name or "",
                model_used=model,
                output="",
                usage=None,
                status="failed",
                error=str(exc),
            )
