"""FastAPI REST API for fertility-sense."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException, Query

from fertility_sense import __version__
from fertility_sense.nemoclaw.agents import ALL_AGENTS
from fertility_sense.nemoclaw.orchestrator import FertilityOrchestrator

app = FastAPI(
    title="Fertility-Sense API",
    version=__version__,
    description="Demand-sensing intelligence platform for fertility and prenatal care",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.get("/agents")
def list_agents() -> list[dict]:
    """List all registered agents."""
    return [
        {
            "name": a.name,
            "role": a.role.value,
            "tier": a.default_tier.value,
            "description": a.description,
            "skills": [s.name for s in a.skills],
            "enabled": a.enabled,
        }
        for a in ALL_AGENTS
    ]


@app.get("/agents/{name}")
def get_agent(name: str) -> dict:
    """Get agent details by name."""
    from fertility_sense.nemoclaw.agents import AGENT_MAP

    agent = AGENT_MAP.get(name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    return {
        "name": agent.name,
        "role": agent.role.value,
        "tier": agent.default_tier.value,
        "description": agent.description,
        "skills": [
            {"name": s.name, "description": s.description, "tags": s.tags}
            for s in agent.skills
        ],
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
    }


@app.post("/pipeline/run")
def run_pipeline() -> dict:
    """Trigger a full pipeline run."""
    orch = FertilityOrchestrator()
    run_id = str(uuid.uuid4())[:8]
    result = orch.execute_pipeline(run_id)
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


@app.get("/feeds/health")
def feeds_health() -> dict:
    """Check feed health status."""
    # In production: query FeedRegistry.health_report()
    return {"status": "no_feeds_configured", "feeds": []}
