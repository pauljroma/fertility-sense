"""Autonomous scout loop — ingests feeds, scores topics, detects velocity changes.

Runs continuously (or once) to detect emerging high-demand fertility topics
and alert when significant TOS swings occur.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fertility_sense.pipeline import Pipeline
from fertility_sense.report import FERTILITY_STAGES

logger = logging.getLogger(__name__)


@dataclass
class VelocityAlert:
    """A topic whose TOS changed by more than the threshold between runs."""

    topic_id: str
    previous_tos: float
    current_tos: float
    delta: float
    direction: str  # "rising" or "falling"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ScoutResult:
    """Result of a single scout run."""

    run_at: str
    topics_scored: int
    feeds_ingested: dict[str, int]
    velocity_alerts: list[VelocityAlert]
    top_scores: list[dict[str, Any]]
    b2b_feed_health: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    error: str | None = None


class ScoutLoop:
    """Autonomous demand-sensing loop.

    Each ``run_once`` call:
    1. Ingests all due feeds via ``Pipeline.ingest()``
    2. Re-scores all fertility topics via ``Pipeline.score()``
    3. Compares current scores to previous scores (stored in score_history.json)
    4. Detects velocity changes (>10 point TOS swing)
    5. Emails alert if new high-demand topic emerges
    6. Saves score history for next comparison
    """

    VELOCITY_THRESHOLD = 10.0  # minimum TOS swing to trigger alert

    def __init__(self, pipeline: Pipeline) -> None:
        self.pipe = pipeline
        self._history_path: Path = (
            pipeline.config.data_dir / "outreach" / "score_history.json"
        )
        # Ensure the outreach directory exists
        self._history_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_once(self) -> ScoutResult:
        """Single scout run: ingest -> score -> detect -> alert."""
        now_iso = datetime.now(timezone.utc).isoformat()
        logger.info("Scout run starting at %s", now_iso)

        # 1. Ingest
        try:
            feed_summary = self.pipe.ingest("all")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            logger.error("Ingestion failed (%s): %s", type(exc).__name__, exc)
            feed_summary = {}
        except Exception as exc:
            logger.error("Ingestion failed (unexpected %s): %s", type(exc).__name__, exc)
            feed_summary = {}

        # 2. Score (top 100 to capture broad picture)
        try:
            scores = self.pipe.score(top_n=100)
        except (OSError, ValueError) as exc:
            logger.error("Scoring failed (%s): %s", type(exc).__name__, exc)
            return ScoutResult(
                run_at=now_iso,
                topics_scored=0,
                feeds_ingested=feed_summary,
                velocity_alerts=[],
                top_scores=[],
                status="error",
                error=str(exc),
            )
        except Exception as exc:
            logger.error("Scoring failed (unexpected %s): %s", type(exc).__name__, exc)
            return ScoutResult(
                run_at=now_iso,
                topics_scored=0,
                feeds_ingested=feed_summary,
                velocity_alerts=[],
                top_scores=[],
                status="error",
                error=str(exc),
            )

        # 3. Filter to fertility-only stages
        fertility_scores = []
        for s in scores:
            topic = self.pipe.graph.get_topic(s.topic_id)
            if topic and topic.journey_stage in FERTILITY_STAGES:
                fertility_scores.append(s)
        scores = fertility_scores

        # 4. Load previous history
        previous = self._load_history()

        # 5. Build current map
        current: dict[str, float] = {s.topic_id: s.composite_tos for s in scores}

        # 6. Detect velocity changes
        alerts = self._detect_velocity_changes(current, previous)

        # 7. Save current as new history
        self._save_history(current, now_iso)

        # 8. Build top scores summary
        top_scores = [
            {
                "topic_id": s.topic_id,
                "composite_tos": round(s.composite_tos, 1),
                "demand": round(s.demand_score, 1),
                "clinical": round(s.clinical_importance, 1),
                "rank": s.rank,
            }
            for s in scores[:20]
        ]

        # 8b. Collect B2B feed health and pipeline metrics
        b2b_health = self._collect_b2b_health()

        result = ScoutResult(
            run_at=now_iso,
            topics_scored=len(scores),
            feeds_ingested=feed_summary,
            velocity_alerts=alerts,
            top_scores=top_scores,
            b2b_feed_health=b2b_health,
        )

        # 9. Email alert if there are velocity alerts
        if alerts:
            try:
                self._email_digest(result)
            except (OSError, ConnectionError) as exc:
                logger.warning("Failed to email scout digest (%s): %s", type(exc).__name__, exc)
            except Exception as exc:
                logger.warning("Failed to email scout digest (unexpected %s): %s", type(exc).__name__, exc)

        logger.info(
            "Scout run complete: %d topics scored, %d alerts",
            len(scores),
            len(alerts),
        )
        return result

    def run_loop(self, interval_hours: float = 6.0) -> None:
        """Continuous loop with sleep between runs."""
        logger.info("Starting scout loop (interval=%.1fh)", interval_hours)
        interval_secs = interval_hours * 3600

        while True:
            try:
                result = self.run_once()
                logger.info(
                    "Scout loop tick: status=%s, alerts=%d",
                    result.status,
                    len(result.velocity_alerts),
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                logger.error("Scout loop error (%s): %s", type(exc).__name__, exc, exc_info=True)
            except Exception as exc:
                logger.error("Scout loop error (unexpected %s): %s", type(exc).__name__, exc, exc_info=True)

            time.sleep(interval_secs)

    # ------------------------------------------------------------------
    # B2B feed health
    # ------------------------------------------------------------------

    def _collect_b2b_health(self) -> dict[str, Any]:
        """Collect health metrics for B2B signal feeds (state mandates, competitor intel)."""
        health: dict[str, Any] = {}

        # State mandate feed health
        try:
            sm_feed = self.pipe.registry.get("state_mandates")
            sm_health = sm_feed.health()
            from fertility_sense.feeds.state_mandates import (
                STATE_MANDATES,
                states_with_ivf_mandate,
            )

            health["state_mandates"] = {
                "status": "OK" if not sm_health.is_stale else "STALE",
                "records_ingested": sm_health.records_ingested,
                "total_mandate_states": len(STATE_MANDATES),
                "ivf_mandate_states": len(states_with_ivf_mandate()),
            }
        except KeyError:
            health["state_mandates"] = {"status": "NOT_REGISTERED"}

        # Competitor intel feed health
        try:
            ci_feed = self.pipe.registry.get("competitor_intel")
            ci_health = ci_feed.health()
            from fertility_sense.feeds.competitor_news import COMPETITORS

            health["competitor_intel"] = {
                "status": "OK" if not ci_health.is_stale else "STALE",
                "records_ingested": ci_health.records_ingested,
                "competitors_tracked": len(COMPETITORS),
            }
        except KeyError:
            health["competitor_intel"] = {"status": "NOT_REGISTERED"}

        # Pipeline metrics (if deal_pipeline module exists)
        try:
            from fertility_sense.outreach.prospect_store import ProspectStore

            store = ProspectStore(self.pipe.config.data_dir / "outreach" / "prospects")
            all_prospects = store.list_all()
            health["pipeline"] = {
                "total_prospects": len(all_prospects),
                "by_stage": {},
            }
            for p in all_prospects:
                stage = getattr(p, "deal_stage", "unknown")
                health["pipeline"]["by_stage"][stage] = (
                    health["pipeline"]["by_stage"].get(stage, 0) + 1
                )
        except (ImportError, OSError, Exception):
            health["pipeline"] = {"status": "unavailable"}

        return health

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _detect_velocity_changes(
        self,
        current: dict[str, float],
        previous: dict[str, float],
    ) -> list[VelocityAlert]:
        """Find topics with >VELOCITY_THRESHOLD point TOS swing."""
        alerts: list[VelocityAlert] = []

        if not previous:
            return alerts  # First run — nothing to compare

        # Only compare topics in CURRENT set (fertility-only).
        # Ignore topics that existed in old history but aren't in current —
        # those are pregnancy/postpartum topics that got filtered out.
        for tid in current:
            cur = current[tid]
            prev = previous.get(tid, 0.0)
            delta = cur - prev

            if abs(delta) >= self.VELOCITY_THRESHOLD:
                alerts.append(
                    VelocityAlert(
                        topic_id=tid,
                        previous_tos=round(prev, 1),
                        current_tos=round(cur, 1),
                        delta=round(delta, 1),
                        direction="rising" if delta > 0 else "falling",
                    )
                )

        # Sort by absolute delta descending
        alerts.sort(key=lambda a: abs(a.delta), reverse=True)
        return alerts

    def _email_digest(self, result: ScoutResult) -> None:
        """Email scout digest to configured address."""
        from fertility_sense.outreach.email_sender import EmailSender, campaign_to_email

        config = self.pipe.config
        sender = EmailSender(config)

        if not sender.test_connection():
            logger.warning("SMTP connection failed — skipping scout email")
            return

        subject = f"Fertility Sense Scout Alert — {len(result.velocity_alerts)} velocity change(s)"
        body_parts = [
            "Fertility Sense — Scout Alert",
            f"Run at: {result.run_at}",
            f"Topics scored: {result.topics_scored}",
            f"Feeds ingested: {json.dumps(result.feeds_ingested)}",
            "",
            "VELOCITY ALERTS (>10 point TOS swing)",
            "-" * 50,
        ]

        for alert in result.velocity_alerts:
            arrow = "^" if alert.direction == "rising" else "v"
            body_parts.append(
                f"  {arrow} {alert.topic_id}: {alert.previous_tos} -> "
                f"{alert.current_tos} ({alert.delta:+.1f})"
            )

        body_parts.extend(["", "TOP 5 SCORES", "-" * 50])
        for s in result.top_scores[:5]:
            body_parts.append(
                f"  #{s['rank']} {s['topic_id']}: TOS={s['composite_tos']}"
            )

        # B2B feed health
        if result.b2b_feed_health:
            body_parts.extend(["", "B2B FEED HEALTH", "-" * 50])
            sm = result.b2b_feed_health.get("state_mandates", {})
            if sm:
                body_parts.append(
                    f"  State Mandates: {sm.get('status', 'N/A')} — "
                    f"{sm.get('total_mandate_states', 0)} mandate states, "
                    f"{sm.get('ivf_mandate_states', 0)} with IVF"
                )
            ci = result.b2b_feed_health.get("competitor_intel", {})
            if ci:
                body_parts.append(
                    f"  Competitor Intel: {ci.get('status', 'N/A')} — "
                    f"{ci.get('competitors_tracked', 0)} competitors tracked"
                )
            pipeline = result.b2b_feed_health.get("pipeline", {})
            if pipeline and pipeline.get("total_prospects") is not None:
                body_parts.append(
                    f"  Pipeline: {pipeline.get('total_prospects', 0)} prospects"
                )

        body = "\n".join(body_parts)
        alert_to = self.pipe.config.alert_email
        email = campaign_to_email(
            to=alert_to,
            subject=subject,
            body=body,
        )
        send_result = sender.send(email)
        if send_result.status == "sent":
            logger.info("Scout alert emailed to %s", alert_to)
        else:
            logger.warning("Scout email failed: %s", send_result.error)

    # ------------------------------------------------------------------
    # Score history persistence
    # ------------------------------------------------------------------

    def _load_history(self) -> dict[str, float]:
        """Load previous score snapshot from disk."""
        if not self._history_path.exists():
            return {}
        try:
            data = json.loads(self._history_path.read_text())
            return data.get("scores", {})
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            logger.warning("Corrupt score history (%s) — starting fresh", type(exc).__name__)
            return {}

    def _save_history(self, scores: dict[str, float], timestamp: str) -> None:
        """Save current score snapshot to disk."""
        data = {
            "timestamp": timestamp,
            "scores": {k: round(v, 2) for k, v in scores.items()},
        }
        _atomic_write_json(self._history_path, data)


def _atomic_write_json(path: Path, data: dict | list) -> None:
    """Write JSON to *path* atomically via rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", dir=path.parent, suffix=".tmp", delete=False
    ) as tmp:
        json.dump(data, tmp, indent=2, default=str)
        tmp.flush()
        os.fsync(tmp.fileno())
    os.replace(tmp.name, str(path))
