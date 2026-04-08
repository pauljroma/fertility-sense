"""Evidence quality evaluation store."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvidenceEvalEntry:
    topic_id: str
    evidence_count: int
    best_grade: str
    coverage_score: float  # 0-1, how well evidence covers the topic
    freshness_score: float  # 0-1, how recent the evidence is
    evaluated_at: datetime = field(default_factory=datetime.utcnow)


class EvidenceEvalStore:
    """Tracks evidence quality evaluations per topic over time."""

    def __init__(self) -> None:
        self._entries: dict[str, list[EvidenceEvalEntry]] = {}

    def record(self, entry: EvidenceEvalEntry) -> None:
        if entry.topic_id not in self._entries:
            self._entries[entry.topic_id] = []
        self._entries[entry.topic_id].append(entry)

    def latest(self, topic_id: str) -> EvidenceEvalEntry | None:
        entries = self._entries.get(topic_id, [])
        return entries[-1] if entries else None

    def coverage_report(self) -> dict[str, float]:
        """Return coverage scores for all evaluated topics."""
        return {
            topic_id: entries[-1].coverage_score
            for topic_id, entries in self._entries.items()
            if entries
        }
