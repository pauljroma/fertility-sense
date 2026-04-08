"""Escalation rules matrix: (risk_tier x evidence_grade) -> action."""

from __future__ import annotations

from enum import Enum

from fertility_sense.governance.evidence_grades import grade_meets_minimum
from fertility_sense.models.evidence import EvidenceGrade
from fertility_sense.models.topic import RiskTier


class EscalationAction(str, Enum):
    AUTO_PUBLISH = "auto_publish"
    PUBLISH_WITH_CAVEAT = "publish_with_caveat"
    AUTO_PUBLISH_WITH_DISCLAIMER = "auto_publish_with_disclaimer"
    ESCALATE_HUMAN_REVIEW = "escalate_human_review"
    REJECT_ALWAYS = "reject_always"


def resolve_escalation(
    risk_tier: RiskTier,
    evidence_grade: EvidenceGrade | None,
) -> EscalationAction:
    """Determine the governance action for a (risk_tier, evidence_grade) pair."""
    # BLACK tier: always reject regardless of evidence
    if risk_tier == RiskTier.BLACK:
        return EscalationAction.REJECT_ALWAYS

    # No evidence at all: escalate for anything above GREEN
    if evidence_grade is None:
        if risk_tier == RiskTier.GREEN:
            return EscalationAction.ESCALATE_HUMAN_REVIEW
        return EscalationAction.ESCALATE_HUMAN_REVIEW

    # X grade (contraindicated): special handling
    if evidence_grade == EvidenceGrade.X:
        return EscalationAction.AUTO_PUBLISH_WITH_DISCLAIMER

    # RED tier
    if risk_tier == RiskTier.RED:
        if grade_meets_minimum(evidence_grade, EvidenceGrade.A):
            return EscalationAction.AUTO_PUBLISH_WITH_DISCLAIMER
        return EscalationAction.ESCALATE_HUMAN_REVIEW

    # YELLOW tier
    if risk_tier == RiskTier.YELLOW:
        if grade_meets_minimum(evidence_grade, EvidenceGrade.B):
            return EscalationAction.AUTO_PUBLISH
        return EscalationAction.ESCALATE_HUMAN_REVIEW

    # GREEN tier
    if grade_meets_minimum(evidence_grade, EvidenceGrade.C):
        return EscalationAction.AUTO_PUBLISH
    return EscalationAction.PUBLISH_WITH_CAVEAT
