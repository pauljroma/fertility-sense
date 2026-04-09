"""Autonomous scout loop — ingests feeds, scores topics, detects velocity changes.

Runs continuously (or once) to detect emerging high-demand fertility topics
and alert when significant TOS swings occur.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fertility_sense.pipeline import Pipeline

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
        except Exception as exc:
            logger.error("Ingestion failed: %s", exc)
            feed_summary = {}

        # 2. Score (top 100 to capture broad picture)
        try:
            scores = self.pipe.score(top_n=100)
        except Exception as exc:
            logger.error("Scoring failed: %s", exc)
            return ScoutResult(
                run_at=now_iso,
                topics_scored=0,
                feeds_ingested=feed_summary,
                velocity_alerts=[],
                top_scores=[],
                status="error",
                error=str(exc),
            )

        # 3. Load previous history
        previous = self._load_history()

        # 4. Build current map
        current: dict[str, float] = {s.topic_id: s.composite_tos for s in scores}

        # 5. Detect velocity changes
        alerts = self._detect_velocity_changes(current, previous)

        # 6. Save current as new history
        self._save_history(current, now_iso)

        # 7. Build top scores summary
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

        result = ScoutResult(
            run_at=now_iso,
            topics_scored=len(scores),
            feeds_ingested=feed_summary,
            velocity_alerts=alerts,
            top_scores=top_scores,
        )

        # 8. Email alert if there are velocity alerts
        if alerts:
            try:
                self._email_digest(result)
            except Exception as exc:
                logger.warning("Failed to email scout digest: %s", exc)

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
            except Exception as exc:
                logger.error("Scout loop error: %s", exc, exc_info=True)

            time.sleep(interval_secs)

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

        all_topics = set(current) | set(previous)
        for tid in all_topics:
            cur = current.get(tid, 0.0)
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

        body = "\n".join(body_parts)
        email = campaign_to_email(
            to="paul@romatech.com",
            subject=subject,
            body=body,
        )
        send_result = sender.send(email)
        if send_result.status == "sent":
            logger.info("Scout alert emailed to paul@romatech.com")
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
        except (json.JSONDecodeError, KeyError):
            logger.warning("Corrupt score history — starting fresh")
            return {}

    def _save_history(self, scores: dict[str, float], timestamp: str) -> None:
        """Save current score snapshot to disk."""
        data = {
            "timestamp": timestamp,
            "scores": {k: round(v, 2) for k, v in scores.items()},
        }
        self._history_path.write_text(json.dumps(data, indent=2))
