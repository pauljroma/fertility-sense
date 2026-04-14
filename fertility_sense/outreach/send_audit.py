"""Immutable send audit log -- records every email send attempt."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel


class SendAuditEntry(BaseModel):
    """A single audit record for an email send attempt."""

    timestamp: str
    recipient: str
    subject: str
    channel: str  # "sequence", "campaign", "digest", "manual"
    status: str  # "sent", "failed", "bounced"
    sequence_name: str = ""
    step_number: int = 0
    campaign_id: str = ""
    error: str = ""
    message_id: str = ""


class SendAuditLog:
    """Append-only JSONL audit log for all outbound email sends.

    Each line is a JSON-serialised ``SendAuditEntry``.  The file is never
    truncated or rewritten -- only appended to.  This makes it safe for
    concurrent processes and trivial to ship to an analytics pipeline later.
    """

    def __init__(self, log_path: Path) -> None:
        self._path = log_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, entry: SendAuditEntry) -> None:
        """Append *entry* to the immutable JSONL log."""
        with open(self._path, "a") as f:
            f.write(entry.model_dump_json() + "\n")

    def query(
        self,
        since: str | None = None,
        recipient: str | None = None,
    ) -> list[SendAuditEntry]:
        """Query audit log with optional filters.

        Args:
            since: ISO-8601 timestamp -- only entries at or after this time.
            recipient: Filter to entries matching this email address.
        """
        if not self._path.exists():
            return []

        entries: list[SendAuditEntry] = []
        with open(self._path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = SendAuditEntry.model_validate_json(line)
                except Exception:
                    continue  # skip corrupt lines

                if since and entry.timestamp < since:
                    continue
                if recipient and entry.recipient != recipient:
                    continue
                entries.append(entry)

        return entries

    def summary(self, days: int = 7) -> dict:
        """Summary stats: total sent/failed, by channel, by recipient.

        Args:
            days: Look back this many days from now.
        """
        from datetime import timedelta

        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).isoformat()

        entries = self.query(since=cutoff)

        total_sent = sum(1 for e in entries if e.status == "sent")
        total_failed = sum(1 for e in entries if e.status == "failed")
        total_bounced = sum(1 for e in entries if e.status == "bounced")

        by_channel: dict[str, int] = {}
        by_recipient: dict[str, int] = {}
        for e in entries:
            by_channel[e.channel] = by_channel.get(e.channel, 0) + 1
            if e.status == "sent":
                by_recipient[e.recipient] = by_recipient.get(e.recipient, 0) + 1

        return {
            "period_days": days,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "total_bounced": total_bounced,
            "by_channel": by_channel,
            "by_recipient": by_recipient,
        }
