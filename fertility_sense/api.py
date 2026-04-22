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

    # ------------------------------------------------------------------
    # Prospects CRUD
    # ------------------------------------------------------------------

    @application.get("/prospects")
    def list_prospects(
        buyer_type: str | None = Query(default=None),
        stage: str | None = Query(default=None),
    ) -> list[dict]:
        """List all prospects, optionally filtered by buyer_type and/or stage."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.prospect_store import ProspectStore

        store = ProspectStore(pipe.config.data_dir / "outreach" / "prospects")
        prospects = store.list_all()
        if buyer_type:
            prospects = [p for p in prospects if p.buyer_type == buyer_type]
        if stage:
            prospects = [p for p in prospects if p.deal_stage == stage]
        return [p.model_dump(mode="json") for p in prospects]

    @application.post("/prospects", status_code=201)
    def create_prospect(data: dict) -> dict:
        """Create a new prospect."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.prospect_store import Prospect, ProspectStore

        store = ProspectStore(pipe.config.data_dir / "outreach" / "prospects")
        if "email" not in data:
            raise HTTPException(status_code=422, detail="Field 'email' is required")
        existing = store.get(data["email"])
        if existing is not None:
            raise HTTPException(
                status_code=409, detail=f"Prospect with email '{data['email']}' already exists"
            )
        prospect = Prospect.model_validate(data)
        store.add(prospect)
        return prospect.model_dump(mode="json")

    @application.patch("/prospects/{email}")
    def update_prospect(email: str, data: dict) -> dict:
        """Update prospect fields by email."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.prospect_store import ProspectStore

        store = ProspectStore(pipe.config.data_dir / "outreach" / "prospects")
        updated = store.update(email, **data)
        if updated is None:
            raise HTTPException(status_code=404, detail=f"Prospect '{email}' not found")
        return updated.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Pipeline Summary
    # ------------------------------------------------------------------

    @application.get("/pipeline/summary")
    def pipeline_summary() -> dict:
        """Pipeline KPIs: total value, deals by stage, weighted value."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.deal_pipeline import DealPipeline
        from fertility_sense.outreach.prospect_store import ProspectStore

        store = ProspectStore(pipe.config.data_dir / "outreach" / "prospects")
        dp = DealPipeline(store)
        return dp.pipeline_summary()

    @application.get("/pipeline/stale")
    def pipeline_stale(days: int = Query(default=30, ge=1)) -> list[dict]:
        """Stale deals — prospects with no activity in N days."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.deal_pipeline import DealPipeline
        from fertility_sense.outreach.prospect_store import ProspectStore

        store = ProspectStore(pipe.config.data_dir / "outreach" / "prospects")
        dp = DealPipeline(store)
        stale = dp.stale_deals(days=days)
        return [p.model_dump(mode="json") for p in stale]

    # ------------------------------------------------------------------
    # Sequences Status
    # ------------------------------------------------------------------

    @application.get("/sequences/status")
    def sequences_status() -> dict:
        """Email sequence enrollment and performance."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.sequences import SequenceEngine

        engine = SequenceEngine(
            sequences_dir=pipe.config.base_dir / "data" / "sequences",
            state_dir=pipe.config.data_dir / "outreach" / "sequence_state",
        )
        return engine.status()

    # ------------------------------------------------------------------
    # Queue Summary
    # ------------------------------------------------------------------

    @application.get("/queue/summary")
    def queue_summary() -> dict:
        """Content queue status and item list."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.content_queue import ContentQueue

        q = ContentQueue(pipe.config.data_dir / "outreach" / "queue")
        items = q.list_all()
        summary = q.summary()
        return {
            "summary": summary,
            "items": [item.model_dump(mode="json") for item in items],
        }

    @application.patch("/queue/{item_id}/approve")
    def approve_queue_item(item_id: str) -> dict:
        """Approve a content queue item."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.content_queue import ContentQueue

        q = ContentQueue(pipe.config.data_dir / "outreach" / "queue")
        ok = q.approve(item_id)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Queue item '{item_id}' not found")
        item = q.get(item_id)
        return item.model_dump(mode="json") if item else {"item_id": item_id, "status": "approved"}

    @application.patch("/queue/{item_id}/reject")
    def reject_queue_item(item_id: str, reason: str = Query(default="")) -> dict:
        """Reject a content queue item."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.content_queue import ContentQueue

        q = ContentQueue(pipe.config.data_dir / "outreach" / "queue")
        ok = q.reject(item_id, reason=reason)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Queue item '{item_id}' not found")
        item = q.get(item_id)
        return item.model_dump(mode="json") if item else {"item_id": item_id, "status": "rejected"}

    # ------------------------------------------------------------------
    # Intelligence (Feeds & Intelligence Dashboard)
    # ------------------------------------------------------------------

    @application.get("/intelligence/summary")
    def intelligence_summary() -> dict:
        """Aggregated intelligence stats for the dashboard."""
        pipe = _get_pipeline()
        records = pipe.evidence_store.all_records()
        all_topics = pipe.graph.all_topics()

        # Grade distribution
        grade_dist: dict[str, int] = {}
        for r in records:
            grade_dist[r.grade.value] = grade_dist.get(r.grade.value, 0) + 1

        # By source
        by_source: dict[str, dict] = {}
        for r in records:
            if r.source_feed not in by_source:
                by_source[r.source_feed] = {"count": 0, "topics": set()}
            by_source[r.source_feed]["count"] += 1
            by_source[r.source_feed]["topics"].update(r.topics)

        source_breakdown = [
            {"source": src, "records": info["count"], "topics_covered": len(info["topics"])}
            for src, info in sorted(by_source.items(), key=lambda x: -x[1]["count"])
        ]

        # Topic coverage
        covered: set[str] = set()
        for r in records:
            covered.update(r.topics)

        return {
            "total_records": len(records),
            "sources_active": len(by_source),
            "topic_coverage_pct": round(len(covered) / len(all_topics) * 100, 1) if all_topics else 0,
            "topics_covered": len(covered),
            "topics_total": len(all_topics),
            "grade_distribution": grade_dist,
            "source_breakdown": source_breakdown,
            "feeds_registered": len(pipe.registry),
        }

    @application.get("/intelligence/coverage")
    def intelligence_coverage() -> dict:
        """Covered vs uncovered topics with evidence counts."""
        pipe = _get_pipeline()
        records = pipe.evidence_store.all_records()
        all_topics = pipe.graph.all_topics()

        # Count evidence per topic
        evidence_by_topic: dict[str, int] = {}
        for r in records:
            for tid in r.topics:
                evidence_by_topic[tid] = evidence_by_topic.get(tid, 0) + 1

        covered = []
        uncovered = []
        for t in all_topics:
            count = evidence_by_topic.get(t.topic_id, 0)
            entry = {
                "topic_id": t.topic_id,
                "display_name": t.display_name,
                "risk_tier": t.risk_tier.value,
                "journey_stage": t.journey_stage.value,
                "evidence_count": count,
            }
            if count > 0:
                covered.append(entry)
            else:
                uncovered.append(entry)

        # Sort covered by count desc, uncovered by risk tier (red first)
        covered.sort(key=lambda x: -x["evidence_count"])
        risk_order = {"red": 0, "yellow": 1, "green": 2, "black": 3}
        uncovered.sort(key=lambda x: risk_order.get(x["risk_tier"], 99))

        return {
            "coverage_pct": round(len(covered) / len(all_topics) * 100, 1) if all_topics else 0,
            "covered": covered,
            "uncovered": uncovered,
        }

    @application.get("/intelligence/by-source")
    def intelligence_by_source() -> dict:
        """Per-source breakdown of ingested evidence."""
        pipe = _get_pipeline()
        records = pipe.evidence_store.all_records()

        by_source: dict[str, dict] = {}
        for r in records:
            if r.source_feed not in by_source:
                by_source[r.source_feed] = {
                    "source": r.source_feed,
                    "record_count": 0,
                    "grades": {},
                    "topics": set(),
                    "latest_date": None,
                }
            info = by_source[r.source_feed]
            info["record_count"] += 1
            info["grades"][r.grade.value] = info["grades"].get(r.grade.value, 0) + 1
            info["topics"].update(r.topics)
            if r.publication_date:
                if info["latest_date"] is None or r.publication_date > info["latest_date"]:
                    info["latest_date"] = r.publication_date

        result = []
        for info in sorted(by_source.values(), key=lambda x: -x["record_count"]):
            result.append({
                "source": info["source"],
                "record_count": info["record_count"],
                "grades": info["grades"],
                "topics_covered": len(info["topics"]),
                "topic_ids": sorted(info["topics"]),
                "latest_date": str(info["latest_date"]) if info["latest_date"] else None,
            })
        return {"sources": result}

    @application.get("/intelligence/evidence")
    def intelligence_evidence(
        topic: str | None = Query(default=None),
        source: str | None = Query(default=None),
        grade: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict:
        """Filterable evidence records."""
        pipe = _get_pipeline()
        records = pipe.evidence_store.all_records()

        if topic:
            records = [r for r in records if topic in r.topics]
        if source:
            records = [r for r in records if r.source_feed == source]
        if grade:
            records = [r for r in records if r.grade.value == grade.upper()]

        records.sort(key=lambda r: r.ingested_at, reverse=True)

        return {
            "total": len(records),
            "records": [
                {
                    "evidence_id": r.evidence_id,
                    "title": r.title,
                    "source_feed": r.source_feed,
                    "grade": r.grade.value,
                    "topics": r.topics,
                    "publication_date": str(r.publication_date) if r.publication_date else None,
                    "key_findings": r.key_findings,
                    "url": r.url,
                    "sample_size": r.sample_size,
                    "limitations": r.limitations,
                }
                for r in records[:limit]
            ],
        }

    # ------------------------------------------------------------------
    # Competitive Intel
    # ------------------------------------------------------------------

    @application.get("/competitive")
    def competitive_landscape() -> dict:
        """Competitor data with WIN positioning."""
        from fertility_sense.feeds.competitor_news import COMPETITORS, win_vs_competitor

        return {
            "competitors": [
                {**v, "key": k, "win_positioning": win_vs_competitor(k)}
                for k, v in COMPETITORS.items()
            ]
        }

    # ------------------------------------------------------------------
    # Regulatory Signals
    # ------------------------------------------------------------------

    @application.get("/regulatory")
    def regulatory_signals() -> dict:
        """State mandate summary for fertility treatment coverage."""
        from fertility_sense.feeds.state_mandates import STATE_MANDATES, states_with_ivf_mandate

        ivf_states = states_with_ivf_mandate()
        return {
            "total_mandate_states": len(STATE_MANDATES),
            "ivf_mandate_states": len(ivf_states),
            "ivf_states": ivf_states,
            "mandates": STATE_MANDATES,
        }

    # ------------------------------------------------------------------
    # Executive Summary (aggregated dashboard)
    # ------------------------------------------------------------------

    @application.get("/executive/summary")
    def executive_summary() -> dict:
        """Executive dashboard: pipeline KPIs + stale deals + competitive + regulatory."""
        pipe = _get_pipeline()
        from fertility_sense.outreach.deal_pipeline import DealPipeline
        from fertility_sense.outreach.prospect_store import ProspectStore
        from fertility_sense.feeds.competitor_news import COMPETITORS
        from fertility_sense.feeds.state_mandates import STATE_MANDATES, states_with_ivf_mandate

        store = ProspectStore(pipe.config.data_dir / "outreach" / "prospects")
        dp = DealPipeline(store)

        summary = dp.pipeline_summary()
        stale = dp.stale_deals(days=30)
        ivf_states = states_with_ivf_mandate()

        return {
            "pipeline": {
                "total_deals": summary.get("total", {}).get("count", 0),
                "total_value": summary.get("total", {}).get("value", 0),
                "weighted_value": summary.get("total", {}).get("weighted", 0),
                "by_stage": {
                    k: v for k, v in summary.items() if k != "total"
                },
            },
            "stale_deals": len(stale),
            "competitive": {
                "tracked_competitors": len(COMPETITORS),
                "names": [v["name"] for v in COMPETITORS.values()],
            },
            "regulatory": {
                "total_mandate_states": len(STATE_MANDATES),
                "ivf_mandate_states": len(ivf_states),
            },
        }

    return application


# Default app instance (used by uvicorn fertility_sense.api:app)
app = create_app()
