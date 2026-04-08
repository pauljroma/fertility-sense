"""FastAPI REST API for fertility-sense."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from fertility_sense import __version__
from fertility_sense.auth import require_api_key, set_config
from fertility_sense.config import FertilitySenseConfig
from fertility_sense.feeds.registry import FeedRegistry
from fertility_sense.nemoclaw.agents import ALL_AGENTS
from fertility_sense.nemoclaw.orchestrator import FertilityOrchestrator

logger = logging.getLogger(__name__)

# Global feed registry — populated on startup, read by /health
_feed_registry = FeedRegistry()

# ---------------------------------------------------------------------------
# Rate limiter (simple in-memory, per-IP)
# ---------------------------------------------------------------------------

_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW = 60.0  # seconds
_RATE_LIMIT_MAX = 60  # requests per window


async def _rate_limit(request: Request) -> None:
    """Enforce per-IP rate limiting (max 60 req/min)."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    timestamps = _rate_limit_store[client_ip]
    # Prune old entries
    _rate_limit_store[client_ip] = [t for t in timestamps if now - t < _RATE_LIMIT_WINDOW]
    if len(_rate_limit_store[client_ip]) >= _RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limited", "message": "Too many requests. Max 60 per minute."},
        )
    _rate_limit_store[client_ip].append(now)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    logger.info("fertility-sense %s starting up", __version__)
    try:
        cfg = FertilitySenseConfig()
        logger.info("Config validated — port=%s, data_dir=%s", cfg.port, cfg.data_dir)
    except Exception:
        logger.warning("Config validation failed (check .env or pydantic-settings)")

    logger.info("Registered %d agent(s), %d feed(s)", len(ALL_AGENTS), len(_feed_registry))
    yield
    logger.info("fertility-sense shutting down gracefully")


def create_app(config: FertilitySenseConfig | None = None) -> FastAPI:
    """Build and return the FastAPI application with security middleware."""
    if config is None:
        config = FertilitySenseConfig()

    # Inject config into auth module
    set_config(config)

    application = FastAPI(
        title="Fertility-Sense API",
        version=__version__,
        description="Demand-sensing intelligence platform for fertility and prenatal care",
        dependencies=[Depends(require_api_key), Depends(_rate_limit)],
        lifespan=lifespan,
    )

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @application.get("/health")
    def health() -> dict:
        feed_health = _feed_registry.health_report()
        agent_count = len(ALL_AGENTS)
        feed_count = len(_feed_registry)

        all_ok = all(not fh.is_stale and fh.last_error is None for fh in feed_health)
        status = "ok" if (all_ok or not feed_health) else "degraded"

        return {
            "status": status,
            "version": __version__,
            "agents": agent_count,
            "feeds": feed_count,
            "feed_details": [
                {
                    "name": fh.feed_name,
                    "ok": not fh.is_stale and fh.last_error is None,
                    "last_success": str(fh.last_success) if fh.last_success else None,
                    "records_ingested": fh.records_ingested,
                }
                for fh in feed_health
            ],
        }

    @application.get("/agents")
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

    @application.get("/agents/{name}")
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

    @application.post("/pipeline/run")
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

    @application.get("/feeds/health")
    def feeds_health() -> dict:
        """Check feed health status."""
        return {"status": "no_feeds_configured", "feeds": []}

    return application


# Default app instance (used by uvicorn fertility_sense.api:app)
app = create_app()
