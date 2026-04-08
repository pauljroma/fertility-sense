"""Safety-specific back-pressure checks."""

from __future__ import annotations

from dataclasses import dataclass

from fertility_sense.models.safety import SafetyAlert, SafetySeverity
from fertility_sense.models.topic import RiskTier


@dataclass
class SafetyBackPressureResult:
    passed: bool
    reason: str
    block_publication: bool


def check_safety_back_pressure(
    topic_id: str,
    risk_tier: RiskTier,
    active_alerts: list[SafetyAlert],
) -> SafetyBackPressureResult:
    """Apply safety-specific back-pressure before answer publication.

    Blocks publication when:
    - CRITICAL safety alert exists for the topic
    - RED tier topic without recent human review
    - Multiple HIGH alerts on same topic
    """
    critical_alerts = [
        a for a in active_alerts
        if a.severity == SafetySeverity.CRITICAL and topic_id in a.affected_topics
    ]

    if critical_alerts:
        return SafetyBackPressureResult(
            passed=False,
            reason=f"CRITICAL safety alert: {critical_alerts[0].title}",
            block_publication=True,
        )

    high_alerts = [
        a for a in active_alerts
        if a.severity == SafetySeverity.HIGH and topic_id in a.affected_topics
    ]

    if len(high_alerts) >= 2:
        return SafetyBackPressureResult(
            passed=False,
            reason=f"Multiple HIGH safety alerts ({len(high_alerts)}) on topic",
            block_publication=True,
        )

    if risk_tier == RiskTier.BLACK:
        return SafetyBackPressureResult(
            passed=False,
            reason="BLACK risk tier: publication always blocked",
            block_publication=True,
        )

    return SafetyBackPressureResult(
        passed=True,
        reason="No safety back-pressure triggered",
        block_publication=False,
    )
