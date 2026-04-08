"""Evidence retrieval for a topic."""

from __future__ import annotations

from dataclasses import dataclass, field

from fertility_sense.models.evidence import EvidenceRecord, EvidenceGrade, EVIDENCE_GRADE_WEIGHTS
from fertility_sense.models.safety import SafetyAlert


@dataclass
class RetrievalResult:
    topic_id: str
    evidence: list[EvidenceRecord] = field(default_factory=list)
    safety_alerts: list[SafetyAlert] = field(default_factory=list)

    @property
    def has_evidence(self) -> bool:
        return len(self.evidence) > 0

    @property
    def best_grade(self) -> EvidenceGrade | None:
        if not self.evidence:
            return None
        non_x = [r for r in self.evidence if r.grade != EvidenceGrade.X]
        if not non_x:
            return EvidenceGrade.X
        return max(non_x, key=lambda r: EVIDENCE_GRADE_WEIGHTS[r.grade]).grade

    @property
    def has_critical_alerts(self) -> bool:
        from fertility_sense.models.safety import SafetySeverity

        return any(a.severity == SafetySeverity.CRITICAL for a in self.safety_alerts)


class EvidenceRetriever:
    """Retrieves evidence records and safety alerts for a topic from in-memory stores."""

    def __init__(
        self,
        evidence_records: list[EvidenceRecord],
        safety_alerts: list[SafetyAlert],
    ) -> None:
        self._evidence = evidence_records
        self._alerts = safety_alerts

    def retrieve(self, topic_id: str, max_evidence: int = 10) -> RetrievalResult:
        """Retrieve evidence and alerts for a topic, sorted by grade then recency."""
        matching_evidence = [
            r for r in self._evidence if topic_id in r.topics
        ]
        # Sort: best grade first, then most recent
        matching_evidence.sort(
            key=lambda r: (
                -EVIDENCE_GRADE_WEIGHTS[r.grade],
                -(r.publication_date.toordinal() if r.publication_date else 0),
            )
        )

        matching_alerts = [
            a for a in self._alerts
            if topic_id in a.affected_topics and not a.resolved
        ]

        return RetrievalResult(
            topic_id=topic_id,
            evidence=matching_evidence[:max_evidence],
            safety_alerts=matching_alerts,
        )
