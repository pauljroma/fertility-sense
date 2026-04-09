"""Content review queue — HITL layer for outreach content.

All composed outreach content goes into a review queue before distribution.
Items are stored as individual JSON files in the queue directory.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

import uuid


class QueueItem(BaseModel):
    """A single piece of content awaiting review."""

    item_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    channel: str  # reddit, email, blog, social, forum, direct_email
    topic_id: str
    title: str
    body: str
    target: str  # subreddit name, email address, blog slug, etc.
    risk_tier: str
    evidence_count: int
    status: str = "pending"  # pending, approved, sent, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: datetime | None = None
    sent_at: datetime | None = None
    rejection_reason: str = ""


class ContentQueue:
    """File-backed content review queue.

    Each item is persisted as ``{queue_dir}/{item_id}.json``.
    """

    def __init__(self, queue_dir: Path) -> None:
        self._dir = queue_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _path(self, item_id: str) -> Path:
        return self._dir / f"{item_id}.json"

    def _save(self, item: QueueItem) -> None:
        self._path(item.item_id).write_text(
            item.model_dump_json(indent=2), encoding="utf-8"
        )

    def _load(self, path: Path) -> QueueItem | None:
        try:
            return QueueItem.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, item: QueueItem) -> str:
        """Persist a new queue item.  Returns the item_id."""
        self._save(item)
        return item.item_id

    def list_pending(self) -> list[QueueItem]:
        """Return all items with status ``pending``."""
        return self.list_all(status="pending")

    def list_all(self, status: str | None = None) -> list[QueueItem]:
        """Return items, optionally filtered by *status*."""
        items: list[QueueItem] = []
        for path in sorted(self._dir.glob("*.json")):
            item = self._load(path)
            if item is None:
                continue
            if status is not None and item.status != status:
                continue
            items.append(item)
        return items

    def get(self, item_id: str) -> QueueItem | None:
        """Look up a single item by id."""
        path = self._path(item_id)
        if not path.exists():
            return None
        return self._load(path)

    def approve(self, item_id: str) -> bool:
        """Mark an item as approved.  Returns False if item not found."""
        item = self.get(item_id)
        if item is None:
            return False
        item.status = "approved"
        item.reviewed_at = datetime.utcnow()
        self._save(item)
        return True

    def reject(self, item_id: str, reason: str = "") -> bool:
        """Reject an item with an optional reason."""
        item = self.get(item_id)
        if item is None:
            return False
        item.status = "rejected"
        item.reviewed_at = datetime.utcnow()
        item.rejection_reason = reason
        self._save(item)
        return True

    def mark_sent(self, item_id: str) -> bool:
        """Mark an approved item as sent."""
        item = self.get(item_id)
        if item is None:
            return False
        item.status = "sent"
        item.sent_at = datetime.utcnow()
        self._save(item)
        return True

    def auto_approve_stale(
        self, max_age_hours: float = 24.0, risk_tier: str = "green"
    ) -> int:
        """Auto-approve GREEN tier items older than *max_age_hours*.

        Returns the number of items approved.
        """
        now = datetime.utcnow()
        count = 0
        for item in self.list_pending():
            if item.risk_tier != risk_tier:
                continue
            age_hours = (now - item.created_at).total_seconds() / 3600.0
            if age_hours >= max_age_hours:
                self.approve(item.item_id)
                count += 1
        return count

    def summary(self) -> dict[str, int]:
        """Return counts keyed by status."""
        counts: dict[str, int] = {}
        for path in self._dir.glob("*.json"):
            item = self._load(path)
            if item is None:
                continue
            counts[item.status] = counts.get(item.status, 0) + 1
        return counts
