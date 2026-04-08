"""Trust / risk scoring: higher scores mean the topic is safer to serve."""

from __future__ import annotations

from fertility_sense.models.evidence import EvidenceGrade
from fertility_sense.models.safety import SafetyAlert, SafetySeverity
from fertility_sense.models.topic import RiskTier

# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------
W_EVIDENCE_FLOOR = 0.35
W_SAFETY_CLEAR = 0.25
W_CONSENSUS = 0.20
W_GOVERNANCE = 0.20

# Grade floors: minimum evidence quality as a 0-1 trust signal.
EVIDENCE_GRADE_FLOOR: dict[EvidenceGrade, float] = {
    EvidenceGrade.A: 1.0,
    EvidenceGrade.B: 0.75,
    EvidenceGrade.C: 0.4,
    EvidenceGrade.D: 0.15,
    EvidenceGrade.X: 0.0,   # Contraindicated → zero trust floor
}

# Hard cap when any CRITICAL alert is active.
CRITICAL_ALERT_CAP = 20.0


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def evidence_grade_floor(min_grade: EvidenceGrade | None) -> float:
    """Map the *weakest* evidence grade to a trust factor.

    If no evidence exists at all, returns 0.0 (no floor).
    """
    if min_grade is None:
        return 0.0
    return EVIDENCE_GRADE_FLOOR.get(min_grade, 0.0)


def safety_clear(active_alerts: list[SafetyAlert]) -> float:
    """1.0 if no active alerts; 0.0 otherwise."""
    return 1.0 if not active_alerts else 0.0


def consensus_score(sources_agree: bool) -> float:
    """Binary consensus: 1.0 when sources agree, 0.3 otherwise."""
    return 1.0 if sources_agree else 0.3


def governance_readiness(has_template: bool, human_reviewed: bool) -> float:
    """Readiness check with two boolean gates.

    - Both true  → 1.0
    - Template only → 0.5
    - Neither → 0.0
    """
    if has_template and human_reviewed:
        return 1.0
    if has_template:
        return 0.5
    return 0.0


def _has_critical_alert(active_alerts: list[SafetyAlert]) -> bool:
    """Return True if any alert is CRITICAL severity."""
    return any(a.severity == SafetySeverity.CRITICAL for a in active_alerts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_trust_score(
    min_evidence_grade: EvidenceGrade | None,
    active_alerts: list[SafetyAlert],
    risk_tier: RiskTier,
    sources_agree: bool,
    has_template: bool,
    human_reviewed: bool,
) -> float:
    """Compute a trust/risk score in [0, 100].  Higher = safer to serve.

    Parameters
    ----------
    min_evidence_grade:
        The *weakest* evidence grade across all records for this topic.
        ``None`` if no evidence exists.
    active_alerts:
        Currently-active safety alerts affecting this topic.
    risk_tier:
        The topic's clinical risk tier.
    sources_agree:
        Whether independent sources converge on the same recommendation.
    has_template:
        Whether an answer-card template exists for this topic.
    human_reviewed:
        Whether a human has signed off on the template / answer.

    Returns
    -------
    float
        Trust score clamped to [0, 100].

    Special Rules
    -------------
    - ``risk_tier == BLACK`` → forced to 0.
    - Any active CRITICAL ``SafetyAlert`` → capped at 20.
    """
    # Hard override: BLACK topics are never safe to serve.
    if risk_tier == RiskTier.BLACK:
        return 0.0

    raw = (
        W_EVIDENCE_FLOOR * evidence_grade_floor(min_evidence_grade)
        + W_SAFETY_CLEAR * safety_clear(active_alerts)
        + W_CONSENSUS * consensus_score(sources_agree)
        + W_GOVERNANCE * governance_readiness(has_template, human_reviewed)
    ) * 100.0

    score = max(0.0, min(raw, 100.0))

    # Cap when any CRITICAL alert is active.
    if _has_critical_alert(active_alerts):
        score = min(score, CRITICAL_ALERT_CAP)

    return score
