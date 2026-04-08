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
from fertility_sense.nemoclaw.agents import ALL_AGENTS

logger = logging.getLogger(__name__)

# Module-level pipeline (set during lifespan startup)
_pipeline: "Pipeline | None" = None

# ---------------------------------------------------------------------------
# Rate limiter (simple in-memory, per-IP)
# ---------------------------------------------------------------------------

_rate_limit_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW = 60.0
_RATE_LIMIT_MAX = 60


async def _rate_limit(request: Request) -> None:
    """Enforce per-IP rate limiting (max 60 req/min)."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    timestamps = _rate_limit_store[client_ip]
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
    global _pipeline
    logger.info("fertility-sense %s starting up", __version__)
    try:
        from fertility_sense.pipeline import Pipeline

        cfg = FertilitySenseConfig()
        _pipeline = Pipeline(cfg)
        health = _pipeline.health()
        logger.info(
            "Pipeline ready — %d topics, %d evidence records, %d feeds, %d agents",
            health["topics"],
            health["evidence_records"],
            health["feeds"],
            health["agents"],
        )
    except Exception:
        logger.warning("Pipeline initialization failed", exc_info=True)

    yield

    logger.info("fertility-sense shutting down gracefully")
    _pipeline = None


def _get_pipeline() -> "Pipeline":
    """Get the pipeline, raising 503 if not initialized."""
    if _pipeline is None:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    return _pipeline


def create_app(config: FertilitySenseConfig | None = None) -> FastAPI:
    """Build and return the FastAPI application with security middleware."""
    if config is None:
        config = FertilitySenseConfig()

    set_config(config)

    application = FastAPI(
        title="Fertility-Sense API",
        version=__version__,
        description="Demand-sensing intelligence platform for fertility and prenatal care",
        dependencies=[Depends(require_api_key), Depends(_rate_limit)],
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Health (no auth)
    # ------------------------------------------------------------------

    @application.get("/health")
    def health() -> dict:
        if _pipeline:
            h = _pipeline.health()
            return {"status": "ok", "version": __version__, **h}
        return {"status": "starting", "version": __version__}

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    @application.get("/agents")
    def list_agents() -> list[dict]:
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

    # ------------------------------------------------------------------
    # Topics + Scoring
    # ------------------------------------------------------------------

    @application.get("/topics")
    def list_topics(
        top: int = Query(default=20, ge=1, le=200),
        stage: str | None = Query(default=None),
    ) -> list[dict]:
        """Return ranked topics with TOS scores."""
        pipe = _get_pipeline()
        scores = pipe.score(top_n=top)
        return [s.model_dump(mode="json") for s in scores]

    @application.get("/topics/{topic_id}")
    def get_topic(topic_id: str) -> dict:
        """Get a single topic with its TOS score."""
        pipe = _get_pipeline()
        scores = pipe.score(topic_id=topic_id)
        if not scores:
            raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' not found")
        return scores[0].model_dump(mode="json")

    @application.get("/topics/{topic_id}/answer")
    def get_answer(
        topic_id: str,
        query: str = Query(description="User query about this topic"),
    ) -> dict:
        """Assemble a governed answer for a topic."""
        pipe = _get_pipeline()
        try:
            result = pipe.answer(topic_id, query)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        return result.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    @application.post("/pipeline/run")
    def run_pipeline() -> dict:
        """Trigger a full pipeline run via the agent server."""
        pipe = _get_pipeline()
        run_id = str(uuid.uuid4())[:8]
        return pipe.run_full(run_id)

    # ------------------------------------------------------------------
    # Feeds
    # ------------------------------------------------------------------

    @application.get("/feeds/health")
    def feeds_health() -> dict:
        """Check feed health status."""
        pipe = _get_pipeline()
        report = pipe.registry.health_report()
        return {
            "feeds": len(report),
            "details": [
                {
                    "name": h.feed_name,
                    "is_stale": h.is_stale,
                    "records_ingested": h.records_ingested,
                    "last_success": str(h.last_success) if h.last_success else None,
                }
                for h in report
            ],
        }

    return application


# Default app instance (used by uvicorn fertility_sense.api:app)
app = create_app()
