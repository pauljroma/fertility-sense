"""Central pipeline — wires feeds, stores, ontology, scoring, and assembly.

Both the CLI and API delegate to this class so the data path is defined once.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

from fertility_sense.assembly.assembler import AnswerAssembler
from fertility_sense.assembly.retriever import EvidenceRetriever
from fertility_sense.config import FertilitySenseConfig
from fertility_sense.feeds.registry import FeedRegistry
from fertility_sense.governance.evidence_grades import floor_grade
from fertility_sense.memory.evidence_store import EvidenceStore
from fertility_sense.memory.feed_state import FeedStateStore
from fertility_sense.memory.signal_store import SignalStore
from fertility_sense.models.answer import GovernedAnswer
from fertility_sense.models.evidence import EvidenceGrade, EvidenceRecord
from fertility_sense.models.safety import SafetyAlert
from fertility_sense.models.scoring import TopicOpportunityScore
from fertility_sense.models.signal import DemandSnapshot, SignalEvent, SignalSource
from fertility_sense.models.topic import TopicNode
from fertility_sense.nemoclaw.server import FertilitySenseServer
from fertility_sense.ontology.graph import TopicGraph
from fertility_sense.ontology.resolver import AliasResolver
from fertility_sense.scoring.clinical import compute_clinical_score
from fertility_sense.scoring.commercial import compute_commercial_score
from fertility_sense.scoring.composite import compute_composite_tos
from fertility_sense.scoring.demand import compute_demand_score
from fertility_sense.scoring.trust import compute_trust_score

logger = logging.getLogger(__name__)

# Default prevalence estimates by risk tier (rough approximations)
_DEFAULT_PREVALENCE: dict[str, float] = {
    "green": 0.02,
    "yellow": 0.05,
    "red": 0.03,
    "black": 0.01,
}

# SERP quality defaults (assume moderate competition)
_DEFAULT_SERP_QUALITY = 0.5


class Pipeline:
    """End-to-end pipeline that owns the full data path.

    Instantiate once, then call ``ingest``, ``score``, ``answer``, etc.
    """

    def __init__(self, config: FertilitySenseConfig | None = None) -> None:
        self.config = config or FertilitySenseConfig()

        # Ontology
        self.graph = TopicGraph(taxonomy_path=self.config.taxonomy_path)
        self.resolver = AliasResolver(self.config.aliases_path)

        # Stores
        self.signal_store = SignalStore(self.config.data_dir / "signals")
        self.evidence_store = EvidenceStore(self.config.evidence_dir)
        self.feed_state = FeedStateStore(self.config.feed_state_dir)

        # Feeds
        self.registry = FeedRegistry()
        self._register_feeds()

        # Agent server (creates ClaudeClient + Dispatcher if API key present)
        self.server = FertilitySenseServer(config=self.config)

        # Safety alerts (in-memory for now)
        self._safety_alerts: list[SafetyAlert] = []

        # Load seed data if evidence store is empty
        self._load_seed_data_if_empty()

    # ------------------------------------------------------------------
    # Feed registration
    # ------------------------------------------------------------------

    def _register_feeds(self) -> None:
        """Register available feeds. MotherToBaby always; others if configured."""
        from fertility_sense.feeds.mother_to_baby import MotherToBabyFeed

        self.registry.register(MotherToBabyFeed())

        # Google Trends (requires pytrends)
        try:
            from fertility_sense.feeds.google_trends import GoogleTrendsFeed

            self.registry.register(GoogleTrendsFeed())
        except ImportError:
            logger.info("pytrends not installed — GoogleTrendsFeed skipped")

        # Reddit (requires credentials)
        if self.config.reddit_client_id and self.config.reddit_client_secret:
            try:
                from fertility_sense.feeds.reddit import RedditFeed

                self.registry.register(RedditFeed(config=self.config))
            except (ImportError, ValueError) as e:
                logger.info("RedditFeed skipped: %s", e)

    # ------------------------------------------------------------------
    # Seed data
    # ------------------------------------------------------------------

    def _load_seed_data_if_empty(self) -> None:
        """Load seed evidence if the evidence store has no records."""
        if self.evidence_store.all_records():
            return
        seed_path = self.config.base_dir / "data" / "seed" / "evidence.yaml"
        if not seed_path.exists():
            return
        try:
            data = yaml.safe_load(seed_path.read_text())
            records = data.get("records", [])
            count = 0
            for raw in records:
                record = EvidenceRecord.model_validate(raw)
                self.evidence_store.put(record)
                count += 1
            logger.info("Loaded %d seed evidence records", count)
        except Exception:
            logger.warning("Failed to load seed data from %s", seed_path, exc_info=True)

    # ------------------------------------------------------------------
    # Ingest
    # ------------------------------------------------------------------

    def ingest(self, feed_name: str = "all") -> dict[str, int]:
        """Run feed ingestion and write results to stores.

        Returns dict of {feed_name: records_ingested}.
        """
        since = datetime.now(tz=timezone.utc) - timedelta(days=7)
        loop = _get_or_create_loop()
        results = loop.run_until_complete(self._async_ingest(feed_name, since))
        return results

    async def _async_ingest(
        self, feed_name: str, since: datetime
    ) -> dict[str, int]:
        summary: dict[str, int] = {}

        if feed_name == "all":
            raw_results = await self.registry.run_all(since)
        else:
            feed = self.registry.get(feed_name)
            records = await feed.ingest(since)
            raw_results = {feed_name: records}

        for fname, records in raw_results.items():
            count = 0
            for record in records:
                if isinstance(record, EvidenceRecord):
                    self.evidence_store.put(record)
                    count += 1
                elif isinstance(record, SignalEvent):
                    self.signal_store.append(record)
                    count += 1
                elif isinstance(record, SafetyAlert):
                    self._safety_alerts.append(record)
                    count += 1
                else:
                    # Unknown model type — still count it
                    count += 1
            summary[fname] = count

        return summary

    # ------------------------------------------------------------------
    # Score
    # ------------------------------------------------------------------

    def score(
        self, topic_id: str = "all", top_n: int = 20
    ) -> list[TopicOpportunityScore]:
        """Compute TOS for topics. Returns sorted list (highest first)."""
        if topic_id != "all":
            topic = self.graph.get_topic(topic_id)
            if topic is None:
                return []
            return [self._score_topic(topic)]

        topics = self.graph.all_topics()
        scores = [self._score_topic(t) for t in topics]
        scores.sort(key=lambda s: s.composite_tos, reverse=True)

        # Assign ranks
        for i, s in enumerate(scores):
            s.rank = i + 1

        return scores[:top_n]

    def _score_topic(self, topic: TopicNode) -> TopicOpportunityScore:
        """Compute all 4 sub-scores + composite for a single topic."""
        period = _current_period()
        evidence = self.evidence_store.by_topic(topic.topic_id)
        alerts = [
            a for a in self._safety_alerts
            if topic.topic_id in a.affected_topics and not a.resolved
        ]

        # Demand score (use defaults if no signal data)
        demand = self._compute_demand(topic, period)

        # Clinical score
        prevalence = _DEFAULT_PREVALENCE.get(topic.risk_tier.value, 0.02)
        clinical = compute_clinical_score(
            records=evidence,
            risk_tier=topic.risk_tier,
            prevalence_pct=prevalence,
        )

        # Trust score
        grades = [r.grade for r in evidence]
        min_grade = floor_grade(grades) if grades else None
        trust = compute_trust_score(
            min_evidence_grade=min_grade,
            active_alerts=alerts,
            risk_tier=topic.risk_tier,
            sources_agree=True,  # Default assumption
            has_template=True,   # Templates exist for all risk tiers
            human_reviewed=False,
        )

        # Commercial score
        commercial = compute_commercial_score(
            monetization_class=topic.monetization_class,
            serp_quality=_DEFAULT_SERP_QUALITY,
            journey_stage=topic.journey_stage,
            intent=topic.intent,
        )

        return compute_composite_tos(
            topic_id=topic.topic_id,
            period=period,
            demand_score=demand,
            clinical_importance=clinical,
            trust_risk_score=trust,
            commercial_fit=commercial,
            config=self.config,
        )

    def _compute_demand(self, topic: TopicNode, period: str) -> float:
        """Compute demand score from signal store, with sensible defaults."""
        # Query signal store for this topic
        now = datetime.now(tz=timezone.utc)
        try:
            signals = self.signal_store.query(now, topic_id=topic.topic_id)
        except Exception:
            signals = []

        if not signals:
            # No signal data — return baseline demand based on topic properties
            # Higher-risk topics get slightly higher baseline (they're searched more)
            base = {"green": 15.0, "yellow": 25.0, "red": 30.0, "black": 10.0}
            return base.get(topic.risk_tier.value, 15.0)

        total_volume = sum(s.volume for s in signals)
        snapshot = DemandSnapshot(
            topic_id=topic.topic_id,
            period=period,
            total_volume=total_volume,
            velocity_7d=0.1,  # Default velocity
            velocity_30d=0.05,
            source_breakdown={s.source: s.volume for s in signals},
            top_queries=[s.raw_query for s in signals[:5]],
        )
        return compute_demand_score(
            snapshot=snapshot,
            p95_volume=max(total_volume, 1000),
            total_sources=5,
            hours_since_first=48.0,
        )

    # ------------------------------------------------------------------
    # Answer
    # ------------------------------------------------------------------

    def answer(self, topic_id: str, query: str) -> GovernedAnswer:
        """Assemble a governed answer with real evidence from the store."""
        topic = self.graph.get_topic(topic_id)
        if topic is None:
            # Try alias resolution
            resolved = self.resolver.resolve(topic_id)
            if resolved:
                topic = self.graph.get_topic(resolved)
        if topic is None:
            raise ValueError(f"Topic '{topic_id}' not found in ontology")

        evidence = self.evidence_store.by_topic(topic.topic_id)
        alerts = [
            a for a in self._safety_alerts
            if topic.topic_id in a.affected_topics and not a.resolved
        ]

        retriever = EvidenceRetriever(
            evidence_records=evidence,
            safety_alerts=alerts,
        )
        assembler = AnswerAssembler(retriever, dispatcher=self.server.dispatcher)
        return assembler.assemble(topic, query)

    # ------------------------------------------------------------------
    # Full pipeline run
    # ------------------------------------------------------------------

    def run_full(self, run_id: str | None = None) -> dict[str, Any]:
        """Run the full intelligence pipeline via the agent server."""
        import uuid

        rid = run_id or str(uuid.uuid4())[:8]
        return self.server.run_pipeline(rid)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """Aggregate health status across all components."""
        feed_health = self.registry.health_report()
        return {
            "topics": len(self.graph),
            "evidence_records": len(self.evidence_store.all_records()),
            "feeds": len(self.registry),
            "feed_details": [
                {"name": h.feed_name, "is_stale": h.is_stale, "records": h.records_ingested}
                for h in feed_health
            ],
            "agents": len(self.server.list_agents()),
            "safety_alerts_active": len(
                [a for a in self._safety_alerts if not a.resolved]
            ),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _current_period() -> str:
    """Return current ISO week string like '2026-W15'."""
    now = date.today()
    return f"{now.year}-W{now.isocalendar()[1]:02d}"


def _get_or_create_loop() -> asyncio.AbstractEventLoop:
    """Get the running event loop or create a new one."""
    try:
        loop = asyncio.get_running_loop()
        # If we're already in an async context, we can't use run_until_complete
        # This shouldn't happen in CLI context
        raise RuntimeError("Cannot run sync pipeline from async context")
    except RuntimeError:
        pass
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop
