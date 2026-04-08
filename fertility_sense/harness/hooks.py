"""Domain lifecycle hooks for the fertility-sense pipeline."""

from __future__ import annotations

from fertility_sense.harness.clinical_drift import ClinicalDriftResult, check_clinical_drift
from fertility_sense.harness.safety_bp import SafetyBackPressureResult, check_safety_back_pressure
from fertility_sense.models.safety import SafetyAlert
from fertility_sense.models.topic import RiskTier


def pre_publish_hook(
    output_text: str,
    topic_id: str,
    risk_tier: RiskTier,
    active_alerts: list[SafetyAlert],
) -> tuple[bool, list[str]]:
    """Pre-publication hook: run clinical drift + safety back-pressure.

    Returns (approved, reasons).
    """
    reasons: list[str] = []

    # Clinical drift check
    drift = check_clinical_drift(output_text, risk_tier)
    if not drift.is_healthy:
        reasons.extend(
            [f"Clinical drift: {v}" for v in drift.safety_violations]
        )

    # Safety back-pressure
    bp = check_safety_back_pressure(topic_id, risk_tier, active_alerts)
    if not bp.passed:
        reasons.append(f"Safety BP: {bp.reason}")

    approved = len(reasons) == 0
    return approved, reasons
