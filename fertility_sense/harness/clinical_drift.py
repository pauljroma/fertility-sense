"""Clinical-specific drift detection.

Extends base drift detection with fertility/prenatal safety awareness.
Detects when agent output drifts from clinical safety boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass

from fertility_sense.governance.disallowed import check_disallowed
from fertility_sense.models.topic import RiskTier


@dataclass
class ClinicalDriftResult:
    drift_score: float  # 0.0 = no drift, 1.0 = severe
    safety_violations: list[str]
    risk_escalated: bool
    should_halt: bool

    @property
    def is_healthy(self) -> bool:
        return self.drift_score < 0.2 and not self.safety_violations


def check_clinical_drift(
    output_text: str,
    intended_risk_tier: RiskTier,
) -> ClinicalDriftResult:
    """Check agent output for clinical safety drift.

    Detects:
    1. Disallowed content patterns (diagnosis, dosage, etc.)
    2. Risk tier violations (generating RED-level content for GREEN topic)
    3. Missing safety language for clinical topics
    """
    violations = check_disallowed(output_text)
    safety_violation_names = [v[0] for v in violations]

    # Compute drift score
    drift_score = 0.0
    if violations:
        drift_score += 0.3 * len(violations)

    # Check for risk escalation indicators
    risk_escalated = False
    if intended_risk_tier == RiskTier.GREEN:
        red_indicators = ["medication", "dosage", "prescri", "diagnosis"]
        if any(ind in output_text.lower() for ind in red_indicators):
            risk_escalated = True
            drift_score += 0.2

    drift_score = min(drift_score, 1.0)
    should_halt = drift_score >= 0.3 or len(violations) >= 2

    return ClinicalDriftResult(
        drift_score=drift_score,
        safety_violations=safety_violation_names,
        risk_escalated=risk_escalated,
        should_halt=should_halt,
    )
