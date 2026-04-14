"""Deal pipeline tracking and reporting for WIN Fertility sales.

Provides pipeline analytics, stage advancement, value estimation,
and formatted reporting on top of the ProspectStore.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fertility_sense.outreach.prospect_store import Prospect, ProspectStore

logger = logging.getLogger(__name__)

# Pipeline value estimates by (buyer_type, company_size) pair.
# For non-CHRO types, company_size key is "" (size-independent).
_ARR_ESTIMATES: dict[tuple[str, str], int] = {
    ("chro", "10000+"): 500_000,
    ("chro", "1000-10000"): 150_000,
    ("chro", "100-1000"): 50_000,
    ("broker", ""): 200_000,
    ("smb", ""): 25_000,
    ("union", ""): 100_000,
    ("tpa", ""): 75_000,
    ("partner", ""): 300_000,
}

# Fallback for unknown buyer types or unmatched combos.
_DEFAULT_ARR = 50_000

# Deal stage close probabilities.
_STAGE_PROBABILITY: dict[str, float] = {
    "cold": 0.05,
    "warm": 0.15,
    "evaluating": 0.35,
    "negotiating": 0.65,
    "won": 1.0,
    "lost": 0.0,
}

# Canonical stage order for display.
_STAGE_ORDER = ["cold", "warm", "evaluating", "negotiating", "won", "lost"]


def _estimate_arr(prospect: Prospect) -> int:
    """Estimate annual recurring revenue for a prospect."""
    # Try exact (buyer_type, company_size) match first.
    key = (prospect.buyer_type, prospect.company_size)
    if key in _ARR_ESTIMATES:
        return _ARR_ESTIMATES[key]
    # Fallback to size-independent key for non-CHRO types.
    key_no_size = (prospect.buyer_type, "")
    if key_no_size in _ARR_ESTIMATES:
        return _ARR_ESTIMATES[key_no_size]
    return _DEFAULT_ARR


def _format_money(value: int | float) -> str:
    """Format a dollar value: $1.2M, $350K, etc."""
    v = float(value)
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:.0f}"


class DealPipeline:
    """Pipeline analytics and stage management built on ProspectStore."""

    def __init__(self, prospect_store: ProspectStore) -> None:
        self.store = prospect_store

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def pipeline_summary(self) -> dict[str, dict]:
        """Pipeline by stage: count, total value, weighted value.

        Returns::

            {
                "cold": {"count": 12, "value": 1200000, "weighted": 60000},
                ...
                "total": {"count": 24, "value": 3400000, "weighted": 1004000},
            }
        """
        prospects = self.store.list_all()
        result: dict[str, dict] = {}

        for stage in _STAGE_ORDER:
            result[stage] = {"count": 0, "value": 0, "weighted": 0}

        for p in prospects:
            stage = p.deal_stage or "cold"
            if stage not in result:
                result[stage] = {"count": 0, "value": 0, "weighted": 0}
            arr = _estimate_arr(p)
            prob = _STAGE_PROBABILITY.get(stage, 0.05)
            result[stage]["count"] += 1
            result[stage]["value"] += arr
            result[stage]["weighted"] += int(arr * prob)

        # Total row.
        total = {"count": 0, "value": 0, "weighted": 0}
        for stage in _STAGE_ORDER:
            total["count"] += result[stage]["count"]
            total["value"] += result[stage]["value"]
            total["weighted"] += result[stage]["weighted"]
        result["total"] = total

        return result

    def pipeline_by_buyer_type(self) -> dict[str, dict]:
        """Pipeline grouped by buyer type.

        Returns::

            {
                "chro": {"count": 5, "value": 1500000, "weighted": 500000},
                ...
            }
        """
        prospects = self.store.list_all()
        result: dict[str, dict] = {}

        for p in prospects:
            bt = p.buyer_type or "unknown"
            if bt not in result:
                result[bt] = {"count": 0, "value": 0, "weighted": 0}
            arr = _estimate_arr(p)
            prob = _STAGE_PROBABILITY.get(p.deal_stage, 0.05)
            result[bt]["count"] += 1
            result[bt]["value"] += arr
            result[bt]["weighted"] += int(arr * prob)

        return result

    def stale_deals(self, days: int = 30) -> list[Prospect]:
        """Prospects with no activity in *days* days."""
        return self.store.stale_prospects(days=days)

    def deal_score(self, prospect: Prospect) -> float:
        """Compute deal probability score (0-100).

        Factors:
        - Stage probability (base)
        - Activity recency bonus
        - Company size bonus (larger = higher intent)
        """
        stage_prob = _STAGE_PROBABILITY.get(prospect.deal_stage, 0.05)
        base = stage_prob * 100  # 0-100

        # Activity recency bonus: up to +15 if activity within 7 days.
        recency_bonus = 0.0
        if prospect.activities:
            last_ts = max(a.get("timestamp", "") for a in prospect.activities)
            try:
                last_dt = datetime.fromisoformat(last_ts)
                if last_dt.tzinfo is None:
                    last_dt = last_dt.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - last_dt).days
                if age <= 7:
                    recency_bonus = 15.0
                elif age <= 14:
                    recency_bonus = 10.0
                elif age <= 30:
                    recency_bonus = 5.0
            except (ValueError, TypeError):
                pass

        # Company size bonus.
        size_bonus = {
            "10000+": 10.0,
            "1000-10000": 7.0,
            "100-1000": 4.0,
            "1-100": 2.0,
        }.get(prospect.company_size, 0.0)

        return min(100.0, base + recency_bonus + size_bonus)

    def auto_advance_stages(self) -> list[str]:
        """Auto-advance deals based on activity patterns.

        Rules:
        - cold -> warm: if any email_opened or replied activity exists
        - warm -> evaluating: if meeting_booked or rfp_received activity exists
        - Mark stale: if no activity in 30 days (adds note, does not change stage)

        Returns list of human-readable change descriptions.
        """
        changes: list[str] = []
        prospects = self.store.list_all()

        for p in prospects:
            if p.deal_stage in ("won", "lost"):
                continue

            actions = {a.get("action", "") for a in p.activities}

            if p.deal_stage == "cold" and actions & {"email_opened", "replied"}:
                old_stage = p.deal_stage
                self.store.update(p.email, deal_stage="warm")
                detail = f"Deal moved {old_stage}->warm (auto: email engagement detected)"
                self.store.log_activity(p.email, "stage_changed", detail, actor="agent:deal-manager")
                changes.append(f"{p.email} ({p.company}): {detail}")

            elif p.deal_stage == "warm" and actions & {"meeting_booked", "rfp_received"}:
                old_stage = p.deal_stage
                self.store.update(p.email, deal_stage="evaluating")
                detail = f"Deal moved {old_stage}->evaluating (auto: meeting/RFP detected)"
                self.store.log_activity(p.email, "stage_changed", detail, actor="agent:deal-manager")
                changes.append(f"{p.email} ({p.company}): {detail}")

        # Flag stale deals.
        stale = self.stale_deals(days=30)
        for p in stale:
            # Only flag once — check if already flagged.
            already_flagged = any(
                a.get("action") == "note_added" and "stale" in a.get("detail", "").lower()
                for a in p.activities
            )
            if not already_flagged:
                detail = "Deal marked stale (no activity in 30+ days)"
                self.store.log_activity(p.email, "note_added", detail, actor="agent:deal-manager")
                changes.append(f"{p.email} ({p.company}): {detail}")

        return changes

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def format_pipeline_report(self) -> str:
        """Human-readable pipeline report for CLI/email."""
        summary = self.pipeline_summary()
        stale = self.stale_deals(days=30)
        by_buyer = self.pipeline_by_buyer_type()

        lines: list[str] = []
        lines.append("")
        lines.append("WIN FERTILITY — DEAL PIPELINE")
        lines.append("=" * 60)
        lines.append(
            f"{'Stage':<16} {'Deals':>5}  {'Value':>12}  {'Weighted':>12}"
        )
        lines.append("-" * 60)

        for stage in _STAGE_ORDER:
            data = summary.get(stage, {"count": 0, "value": 0, "weighted": 0})
            weighted_str = "--" if stage == "lost" else _format_money(data["weighted"])
            lines.append(
                f"{stage:<16} {data['count']:>5}  {_format_money(data['value']):>12}  {weighted_str:>12}"
            )

        lines.append("-" * 60)
        total = summary["total"]
        lines.append(
            f"{'TOTAL':<16} {total['count']:>5}  {_format_money(total['value']):>12}  "
            f"{_format_money(total['weighted']):>12} (weighted)"
        )

        # Stale deals.
        stale_value = sum(_estimate_arr(p) for p in stale)
        lines.append(
            f"{'STALE (30d)':<16} {len(stale):>5}  {_format_money(stale_value):>12}"
        )

        # By buyer type.
        lines.append("")
        lines.append("BY BUYER TYPE")
        lines.append("-" * 60)
        lines.append(
            f"{'Buyer Type':<16} {'Deals':>5}  {'Value':>12}  {'Weighted':>12}"
        )
        lines.append("-" * 60)
        for bt in sorted(by_buyer.keys()):
            data = by_buyer[bt]
            lines.append(
                f"{bt:<16} {data['count']:>5}  {_format_money(data['value']):>12}  "
                f"{_format_money(data['weighted']):>12}"
            )

        # Recent activity summary.
        lines.append("")
        lines.append("RECENT ACTIVITY (7 days)")
        lines.append("-" * 60)
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        action_counts: dict[str, int] = {}
        for p in self.store.list_all():
            for a in p.activities:
                ts_str = a.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts >= cutoff:
                        act = a.get("action", "unknown")
                        action_counts[act] = action_counts.get(act, 0) + 1
                except (ValueError, TypeError):
                    continue

        if action_counts:
            parts = [f"{count} {action}" for action, count in sorted(action_counts.items())]
            lines.append(f"  {', '.join(parts)}")
        else:
            lines.append("  No recent activity.")

        lines.append("")
        return "\n".join(lines)

    def pipeline_digest_section(self) -> str:
        """Compact pipeline summary for inclusion in daily/weekly digests."""
        summary = self.pipeline_summary()
        stale = self.stale_deals(days=30)

        parts: list[str] = []
        for stage in _STAGE_ORDER:
            data = summary.get(stage, {"count": 0, "value": 0})
            if data["count"] > 0:
                parts.append(f"{stage}: {data['count']} ({_format_money(data['value'])})")

        total = summary["total"]

        # Recent activity summary.
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        action_counts: dict[str, int] = {}
        for p in self.store.list_all():
            for a in p.activities:
                ts_str = a.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts >= cutoff:
                        act = a.get("action", "unknown")
                        action_counts[act] = action_counts.get(act, 0) + 1
                except (ValueError, TypeError):
                    continue

        activity_parts = []
        for action in ["email_sent", "replied", "meeting_booked"]:
            count = action_counts.get(action, 0)
            label = action.replace("_", " ") + "s" if count != 1 else action.replace("_", " ")
            activity_parts.append(f"{count} {label}")

        lines = [
            " | ".join(parts) if parts else "No deals in pipeline",
            f"Weighted pipeline: {_format_money(total['weighted'])}",
            f"Stale deals (30d): {len(stale)}",
            f"Recent activity: {', '.join(activity_parts)}" if activity_parts else "Recent activity: none",
        ]
        return "\n".join(lines)
