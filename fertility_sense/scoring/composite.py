"""Composite Topic Opportunity Score (TOS) aggregator."""

from __future__ import annotations

from datetime import datetime

from fertility_sense.config import FertilitySenseConfig
from fertility_sense.models.scoring import TopicOpportunityScore

# Default weights (mirrored from FertilitySenseConfig defaults).
_DEFAULT_W_DEMAND = 0.30
_DEFAULT_W_CLINICAL = 0.25
_DEFAULT_W_TRUST = 0.25
_DEFAULT_W_COMMERCIAL = 0.20

# Default gate thresholds.
_DEFAULT_TRUST_BLOCK = 20.0
_DEFAULT_CLINICAL_ESCALATION = 80.0
_DEFAULT_TRUST_ESCALATION = 40.0


def compute_composite_tos(
    topic_id: str,
    period: str,
    demand_score: float,
    clinical_importance: float,
    trust_risk_score: float,
    commercial_fit: float,
    config: FertilitySenseConfig | None = None,
) -> TopicOpportunityScore:
    """Aggregate the four pillar scores into a single Topic Opportunity Score.

    Parameters
    ----------
    topic_id:
        Canonical topic identifier.
    period:
        Scoring period label (e.g. ``'2026-W14'``).
    demand_score:
        Demand pillar score [0, 100].
    clinical_importance:
        Clinical importance pillar score [0, 100].
    trust_risk_score:
        Trust/risk pillar score [0, 100].  Higher = safer.
    commercial_fit:
        Commercial fit pillar score [0, 100].
    config:
        Optional application config for custom weights and thresholds.

    Returns
    -------
    TopicOpportunityScore
        Fully populated scoring model with gates evaluated.
    """
    # Resolve weights and thresholds from config or defaults.
    if config is not None:
        w_demand = config.w_demand
        w_clinical = config.w_clinical
        w_trust = config.w_trust
        w_commercial = config.w_commercial
        trust_block = config.trust_block_threshold
        clinical_esc = config.clinical_escalation_threshold
        trust_esc = config.trust_escalation_threshold
    else:
        w_demand = _DEFAULT_W_DEMAND
        w_clinical = _DEFAULT_W_CLINICAL
        w_trust = _DEFAULT_W_TRUST
        w_commercial = _DEFAULT_W_COMMERCIAL
        trust_block = _DEFAULT_TRUST_BLOCK
        clinical_esc = _DEFAULT_CLINICAL_ESCALATION
        trust_esc = _DEFAULT_TRUST_ESCALATION

    # Weighted composite.
    composite = (
        w_demand * demand_score
        + w_clinical * clinical_importance
        + w_trust * trust_risk_score
        + w_commercial * commercial_fit
    )
    composite = max(0.0, min(composite, 100.0))

    # Safety gates.
    unsafe_to_serve = trust_risk_score < trust_block
    escalate_to_human = (
        clinical_importance > clinical_esc and trust_risk_score < trust_esc
    )

    return TopicOpportunityScore(
        topic_id=topic_id,
        period=period,
        demand_score=demand_score,
        clinical_importance=clinical_importance,
        trust_risk_score=trust_risk_score,
        commercial_fit=commercial_fit,
        composite_tos=round(composite, 2),
        unsafe_to_serve=unsafe_to_serve,
        escalate_to_human=escalate_to_human,
        computed_at=datetime.utcnow(),
        inputs={
            "weights": {
                "demand": w_demand,
                "clinical": w_clinical,
                "trust": w_trust,
                "commercial": w_commercial,
            },
        },
    )
