"""Clinical importance scoring: evidence density, risk tier, prevalence, and recency."""

from __future__ import annotations

import math
from datetime import date, timedelta
from statistics import median

from fertility_sense.models.evidence import (
    EVIDENCE_GRADE_WEIGHTS,
    EvidenceRecord,
)
from fertility_sense.models.topic import RiskTier

# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------
W_EVIDENCE_DENSITY = 0.40
W_RISK_TIER = 0.25
W_PREVALENCE = 0.20
W_RECENCY = 0.15

# Maximum expected weighted-evidence sum used to normalise evidence density.
# Represents ~10 grade-A records.
MAX_EXPECTED_EVIDENCE = 10.0

# Risk-tier numeric mapping
RISK_TIER_WEIGHT: dict[RiskTier, float] = {
    RiskTier.GREEN: 0.3,
    RiskTier.YELLOW: 0.6,
    RiskTier.RED: 1.0,
    RiskTier.BLACK: 1.0,
}

# Prevalence threshold: 10 % of the population maps to a score of 1.0.
PREVALENCE_CAP = 0.10

# Evidence recency: full freshness within 1 year, decays over 5 years.
RECENCY_FULL_DAYS = 365
RECENCY_HORIZON_DAYS = 5 * 365


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def evidence_density(
    records: list[EvidenceRecord],
    grade_weights: dict | None = None,
) -> float:
    """Weighted density of available evidence, capped at 1.0.

    Each record contributes its grade weight; the sum is divided by
    ``MAX_EXPECTED_EVIDENCE``.
    """
    if not records:
        return 0.0
    weights = grade_weights or EVIDENCE_GRADE_WEIGHTS
    total = sum(weights.get(r.grade, 0.0) for r in records)
    return min(total / MAX_EXPECTED_EVIDENCE, 1.0)


def risk_tier_weight(risk_tier: RiskTier) -> float:
    """Numeric weight for a risk tier."""
    return RISK_TIER_WEIGHT.get(risk_tier, 0.0)


def prevalence_score(affected_population_pct: float) -> float:
    """Linear scale capped at ``PREVALENCE_CAP`` (10 %).

    A prevalence of 10 %+ maps to 1.0.
    """
    if affected_population_pct <= 0.0:
        return 0.0
    return min(affected_population_pct / PREVALENCE_CAP, 1.0)


def recency_of_evidence(
    records: list[EvidenceRecord],
    reference_date: date,
) -> float:
    """Score based on the median publication date of available evidence.

    Returns 1.0 when median is within the last year, decaying linearly to
    0.0 over ``RECENCY_HORIZON_DAYS`` (5 years).
    """
    pub_dates = [r.publication_date for r in records if r.publication_date is not None]
    if not pub_dates:
        return 0.0

    med = _median_date(pub_dates)
    age_days = (reference_date - med).days
    if age_days <= RECENCY_FULL_DAYS:
        return 1.0
    if age_days >= RECENCY_HORIZON_DAYS:
        return 0.0
    # Linear decay between 1 year and 5 years
    return 1.0 - (age_days - RECENCY_FULL_DAYS) / (RECENCY_HORIZON_DAYS - RECENCY_FULL_DAYS)


def _median_date(dates: list[date]) -> date:
    """Compute the median of a list of dates."""
    ordinals = sorted(d.toordinal() for d in dates)
    med_ordinal = median(ordinals)
    return date.fromordinal(int(med_ordinal))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_clinical_score(
    records: list[EvidenceRecord],
    risk_tier: RiskTier,
    prevalence_pct: float,
    reference_date: date | None = None,
) -> float:
    """Compute a clinical importance score in [0, 100].

    Parameters
    ----------
    records:
        Evidence records relevant to the topic.
    risk_tier:
        The topic's clinical risk tier.
    prevalence_pct:
        Estimated fraction of the target population affected (0.0 – 1.0).
    reference_date:
        Date used as "today" for recency calculations.  Defaults to
        ``date.today()``.

    Returns
    -------
    float
        Clinical importance score clamped to [0, 100].
    """
    if reference_date is None:
        reference_date = date.today()

    raw = (
        W_EVIDENCE_DENSITY * evidence_density(records)
        + W_RISK_TIER * risk_tier_weight(risk_tier)
        + W_PREVALENCE * prevalence_score(prevalence_pct)
        + W_RECENCY * recency_of_evidence(records, reference_date)
    ) * 100.0

    return max(0.0, min(raw, 100.0))
