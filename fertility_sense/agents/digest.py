"""Scheduled digest generator — daily and weekly intelligence summaries.

Generates human-readable digest reports from pipeline state and emails
them on a schedule.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fertility_sense.pipeline import Pipeline

logger = logging.getLogger(__name__)


class DigestGenerator:
    """Generate and send daily/weekly intelligence digests."""

    def __init__(self, pipeline: Pipeline) -> None:
        self.pipe = pipeline
        self._history_path: Path = (
            pipeline.config.data_dir / "outreach" / "score_history.json"
        )

    # ------------------------------------------------------------------
    # Daily digest
    # ------------------------------------------------------------------

    def daily_digest(self) -> str:
        """Generate daily digest: new signals, velocity changes, feed health, queue status."""
        now = datetime.now(timezone.utc)
        lines: list[str] = []

        lines.append("=" * 70)
        lines.append("FERTILITY SENSE — DAILY DIGEST")
        lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("=" * 70)

        # --- Feed health ---
        lines.append("")
        lines.append("FEED HEALTH")
        lines.append("-" * 40)
        health = self.pipe.health()
        for fd in health.get("feed_details", []):
            status = "STALE" if fd["is_stale"] else "OK"
            lines.append(f"  {fd['name']:<25} {fd['records']:>4} records  [{status}]")
        lines.append(f"  Total feeds: {health['feeds']}")

        # --- Top 5 TOS scores with changes (fertility-only) ---
        lines.append("")
        lines.append("TOP 5 FERTILITY TOPIC OPPORTUNITY SCORES")
        lines.append("-" * 40)
        scores = self._fertility_scores(top_n=5)
        previous = self._load_previous_scores()

        for s in scores:
            prev_tos = previous.get(s.topic_id, 0.0)
            delta = s.composite_tos - prev_tos
            delta_str = f" ({delta:+.1f})" if previous else ""
            lines.append(
                f"  #{s.rank:<3} {s.topic_id:<30} TOS={s.composite_tos:.1f}{delta_str}"
            )

        # --- Velocity alerts ---
        lines.append("")
        lines.append("VELOCITY ALERTS (>10 point TOS swing)")
        lines.append("-" * 40)
        if previous:
            current_map = {s.topic_id: s.composite_tos for s in self._fertility_scores(top_n=100)}
            alert_count = 0
            for tid, cur in current_map.items():
                prev = previous.get(tid, 0.0)
                delta = cur - prev
                if abs(delta) >= 10.0:
                    arrow = "^" if delta > 0 else "v"
                    lines.append(
                        f"  {arrow} {tid}: {prev:.1f} -> {cur:.1f} ({delta:+.1f})"
                    )
                    alert_count += 1
            if alert_count == 0:
                lines.append("  No velocity alerts.")
        else:
            lines.append("  No previous data — first run.")

        # --- Regulatory signals ---
        lines.append("")
        lines.append("REGULATORY SIGNALS")
        lines.append("-" * 40)
        try:
            from fertility_sense.feeds.state_mandates import (
                STATE_MANDATES,
                states_with_ivf_mandate,
            )

            total_mandates = len(STATE_MANDATES)
            ivf_states = states_with_ivf_mandate()
            lines.append(f"  {total_mandates} states with fertility coverage mandates")
            lines.append(f"  {len(ivf_states)} states with IVF mandate: {', '.join(ivf_states)}")
            key_states = [s for s in ["CA", "NY", "IL", "NJ", "MA"] if s in ivf_states]
            if key_states:
                lines.append(
                    f"  Key states for WIN: {', '.join(key_states)} "
                    f"(large employer base + mandate)"
                )
        except ImportError:
            lines.append("  State mandate feed not available.")

        # --- Competitive landscape ---
        lines.append("")
        lines.append("COMPETITIVE LANDSCAPE")
        lines.append("-" * 40)
        try:
            from fertility_sense.feeds.competitor_news import COMPETITORS

            for _key, comp in COMPETITORS.items():
                name = comp["name"]
                revenue = comp["est_revenue"]
                clients = comp["est_clients"]
                positioning = comp["win_positioning"]
                short_pos = positioning.split(" — ")[0] if " — " in positioning else positioning
                if len(short_pos) > 80:
                    short_pos = short_pos[:77] + "..."
                lines.append(f"  {name}: {revenue}, {clients}")
                lines.append(f"    WIN positioning: {short_pos}")
        except ImportError:
            lines.append("  Competitor intel feed not available.")

        # --- Evidence store count ---
        lines.append("")
        lines.append("EVIDENCE STORE")
        lines.append("-" * 40)
        evidence_count = len(self.pipe.evidence_store.all_records())
        lines.append(f"  Total evidence records: {evidence_count}")

        # --- Content queue status ---
        lines.append("")
        lines.append("CONTENT QUEUE STATUS")
        lines.append("-" * 40)
        queue_status = self._check_queue_status()
        lines.append(f"  Pending:  {queue_status['pending']}")
        lines.append(f"  Approved: {queue_status['approved']}")
        lines.append(f"  Sent:     {queue_status['sent']}")

        # --- Deal pipeline ---
        lines.append("")
        lines.append("DEAL PIPELINE")
        lines.append("-" * 40)
        pipeline_text = self._pipeline_digest()
        for line in pipeline_text.splitlines():
            lines.append(f"  {line}")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Weekly digest
    # ------------------------------------------------------------------

    def weekly_digest(self) -> str:
        """Generate weekly digest: full signal report + recommended actions."""
        from fertility_sense.report import FERTILITY_STAGES, generate_report

        now = datetime.now(timezone.utc)
        lines: list[str] = []

        lines.append("=" * 70)
        lines.append("FERTILITY SENSE — WEEKLY DIGEST")
        lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("=" * 70)

        # --- Full signal report (fertility-only, top 15) ---
        report = generate_report(self.pipe, top_n=15)

        lines.append("")
        lines.append("SIGNAL REPORT (fertility-focused, top 15)")
        lines.append("-" * 50)
        lines.append(f"Total topics: {report.total_topics}")
        lines.append(f"Fertility topics: {report.fertility_topics}")
        lines.append(f"Summary: {report.summary}")
        lines.append("")

        for sig in report.audience_signals:
            flag_str = f" [{', '.join(sig.flags)}]" if sig.flags else ""
            lines.append(f"  {sig.display_name}{flag_str}")
            lines.append(f"    Who: {sig.who}")
            lines.append(f"    Struggle: {sig.struggle}")
            lines.append(
                f"    Demand={sig.demand_score:.0f} | Clinical={sig.clinical_importance:.0f} | "
                f"Evidence={sig.evidence_count}"
            )
            lines.append(f"    Action: {sig.outreach_action}")
            lines.append("")

        # --- Recommended campaign actions ---
        lines.append("RECOMMENDED CAMPAIGN ACTIONS")
        lines.append("-" * 50)
        actionable = [
            s for s in report.audience_signals
            if "BLOCKED" not in s.flags and "NO_EVIDENCE" not in s.flags
        ]
        for i, sig in enumerate(actionable[:5], 1):
            lines.append(f"  {i}. {sig.outreach_action}")
        if not actionable:
            lines.append("  No actionable signals this week.")

        # --- Evidence gaps ---
        lines.append("")
        lines.append("EVIDENCE GAPS")
        lines.append("-" * 50)
        if report.evidence_gaps:
            for gap in report.evidence_gaps:
                lines.append(
                    f"  ! {gap['display_name']} ({gap['risk_tier']}) — {gap['action']}"
                )
        else:
            lines.append("  No evidence gaps.")

        # --- Deal pipeline ---
        lines.append("")
        lines.append("DEAL PIPELINE")
        lines.append("-" * 50)
        pipeline_text = self._pipeline_digest()
        for line in pipeline_text.splitlines():
            lines.append(f"  {line}")

        # --- Week-over-week TOS trends ---
        lines.append("")
        lines.append("WEEK-OVER-WEEK TOS TRENDS")
        lines.append("-" * 50)
        previous = self._load_previous_scores()
        scores = self._fertility_scores(top_n=15)
        if previous:
            for s in scores:
                prev = previous.get(s.topic_id, 0.0)
                delta = s.composite_tos - prev
                trend = "^" if delta > 1 else ("v" if delta < -1 else "=")
                lines.append(
                    f"  {trend} {s.topic_id:<30} {prev:.1f} -> {s.composite_tos:.1f} ({delta:+.1f})"
                )
        else:
            lines.append("  No previous week data for comparison.")

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Send
    # ------------------------------------------------------------------

    def send_digest(self, digest_type: str = "daily", to: str = "paul@romatech.com") -> None:
        """Generate and email the digest."""
        from fertility_sense.outreach.email_sender import EmailSender, campaign_to_email

        if digest_type == "weekly":
            body = self.weekly_digest()
            subject = f"Fertility Sense — Weekly Digest ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})"
        else:
            body = self.daily_digest()
            subject = f"Fertility Sense — Daily Digest ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})"

        config = self.pipe.config
        sender = EmailSender(config)

        if not sender.test_connection():
            logger.error("SMTP connection failed — cannot send digest")
            return

        email = campaign_to_email(to=to, subject=subject, body=body)
        result = sender.send(email)

        if result.status == "sent":
            logger.info("Digest (%s) sent to %s", digest_type, to)
        else:
            logger.error("Digest send failed: %s", result.error)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fertility_scores(self, top_n: int = 5):
        """Score only fertility-focused topics (preconception, trying, treatment)."""
        from fertility_sense.models.topic import JourneyStage
        from fertility_sense.report import FERTILITY_STAGES

        all_scores = self.pipe.score(top_n=200)
        fertility = []
        for s in all_scores:
            topic = self.pipe.graph.get_topic(s.topic_id)
            if topic and topic.journey_stage in FERTILITY_STAGES:
                fertility.append(s)
        # Re-rank
        for i, s in enumerate(fertility[:top_n]):
            s.rank = i + 1
        return fertility[:top_n]

    def _load_previous_scores(self) -> dict[str, float]:
        """Load previous score history for comparison."""
        if not self._history_path.exists():
            return {}
        try:
            data = json.loads(self._history_path.read_text())
            return data.get("scores", {})
        except (json.JSONDecodeError, KeyError):
            return {}

    def _pipeline_digest(self) -> str:
        """Generate compact pipeline summary for digest inclusion."""
        try:
            from fertility_sense.outreach.deal_pipeline import DealPipeline
            from fertility_sense.outreach.prospect_store import ProspectStore

            store = ProspectStore(self.pipe.config.data_dir / "outreach" / "prospects")
            dp = DealPipeline(store)
            return dp.pipeline_digest_section()
        except Exception as exc:
            logger.warning("Failed to generate pipeline digest: %s", exc)
            return "Pipeline data unavailable."

    def _check_queue_status(self) -> dict[str, int]:
        """Count items in the content queue by status."""
        queue_dir = self.pipe.config.data_dir / "outreach" / "queue"
        counts = {"pending": 0, "approved": 0, "sent": 0}

        if not queue_dir.exists():
            return counts

        for f in queue_dir.iterdir():
            if not f.suffix == ".json":
                continue
            try:
                item = json.loads(f.read_text())
                status = item.get("status", "pending")
                if status in counts:
                    counts[status] += 1
                else:
                    counts["pending"] += 1
            except (json.JSONDecodeError, OSError):
                continue

        return counts
