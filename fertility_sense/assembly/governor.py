"""Governance gate — final check before answer publication."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from fertility_sense.assembly.retriever import RetrievalResult
from fertility_sense.governance.disallowed import check_disallowed
from fertility_sense.governance.escalation import EscalationAction, resolve_escalation
from fertility_sense.governance.evidence_grades import floor_grade, grade_meets_minimum
from fertility_sense.models.answer import AnswerTemplate, GovernedAnswer, Provenance
from fertility_sense.models.evidence import EvidenceGrade
from fertility_sense.models.topic import RiskTier


@dataclass
class GovernanceResult:
    passed: bool
    action: EscalationAction
    status: str  # "published", "pending_review", "escalated", "withdrawn"
    reasons: list[str] = field(default_factory=list)


def run_governance_gate(
    sections: dict[str, str],
    template: AnswerTemplate,
    retrieval: RetrievalResult,
    risk_tier: RiskTier,
) -> GovernanceResult:
    """Run the governance gate on assembled answer sections.

    Checks:
    1. Evidence grade meets template minimum
    2. No active CRITICAL safety alerts without handling
    3. No disallowed content patterns
    4. Provenance completeness
    """
    reasons: list[str] = []

    # 1. Evidence grade check
    grades = [r.grade for r in retrieval.evidence]
    min_grade = floor_grade(grades) if grades else None
    escalation = resolve_escalation(risk_tier, min_grade)

    if escalation == EscalationAction.REJECT_ALWAYS:
        return GovernanceResult(
            passed=False,
            action=escalation,
            status="withdrawn",
            reasons=["BLACK tier: always rejected"],
        )

    if min_grade and not grade_meets_minimum(min_grade, template.required_evidence_grade):
        reasons.append(
            f"Evidence grade {min_grade.value} below template minimum "
            f"{template.required_evidence_grade.value}"
        )

    # 2. Critical safety alerts
    if retrieval.has_critical_alerts:
        alert_titles = [a.title for a in retrieval.safety_alerts]
        reasons.append(f"Active CRITICAL safety alerts: {', '.join(alert_titles)}")

    # 3. Disallowed content check
    full_text = " ".join(sections.values())
    violations = check_disallowed(full_text)
    for class_name, matched, _ in violations:
        reasons.append(f"Disallowed content [{class_name}]: '{matched}'")

    # 4. No evidence at all
    if not retrieval.has_evidence and risk_tier != RiskTier.GREEN:
        reasons.append("No evidence records for non-GREEN topic")

    # Determine final status
    if reasons:
        if escalation in (
            EscalationAction.ESCALATE_HUMAN_REVIEW,
            EscalationAction.REJECT_ALWAYS,
        ):
            return GovernanceResult(
                passed=False,
                action=escalation,
                status="escalated",
                reasons=reasons,
            )
        # Has reasons but action is publish — still escalate
        return GovernanceResult(
            passed=False,
            action=EscalationAction.ESCALATE_HUMAN_REVIEW,
            status="escalated",
            reasons=reasons,
        )

    # Passed all checks
    if escalation == EscalationAction.ESCALATE_HUMAN_REVIEW:
        return GovernanceResult(
            passed=False,
            action=escalation,
            status="pending_review",
            reasons=["Escalation required by governance matrix"],
        )

    status = "published"
    return GovernanceResult(
        passed=True,
        action=escalation,
        status=status,
        reasons=[],
    )


def build_provenance(
    retrieval: RetrievalResult,
    reviewer: str = "answer-assembler",
) -> Provenance:
    """Build provenance metadata from retrieval results."""
    grades = [r.grade for r in retrieval.evidence]
    return Provenance(
        evidence_ids=[r.evidence_id for r in retrieval.evidence],
        grade=floor_grade(grades) or EvidenceGrade.D,
        sources=list({r.source_feed for r in retrieval.evidence}),
        last_reviewed=datetime.utcnow(),
        reviewer=reviewer,
    )
