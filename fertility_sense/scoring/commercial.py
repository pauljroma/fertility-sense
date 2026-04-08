"""Commercial fit scoring: monetization, competition gap, audience match, conversion affinity."""

from __future__ import annotations

from fertility_sense.models.topic import JourneyStage, MonetizationClass, TopicIntent

# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------
W_MONETIZATION = 0.30
W_COMPETITION_GAP = 0.25
W_AUDIENCE_MATCH = 0.25
W_CONVERSION = 0.20

# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

MONETIZATION_POTENTIAL: dict[MonetizationClass, float] = {
    MonetizationClass.COMMERCE: 1.0,
    MonetizationClass.REFERRAL: 0.8,
    MonetizationClass.TOOL: 0.6,
    MonetizationClass.CONTENT: 0.3,
    MonetizationClass.NONE: 0.0,
}

AUDIENCE_MATCH: dict[JourneyStage, float] = {
    JourneyStage.TRYING: 1.0,
    JourneyStage.FERTILITY_TREATMENT: 1.0,
    JourneyStage.PRECONCEPTION: 0.8,
    JourneyStage.PREGNANCY_T1: 0.7,
    JourneyStage.PREGNANCY_T2: 0.6,
    JourneyStage.PREGNANCY_T3: 0.6,
    JourneyStage.LABOR_DELIVERY: 0.4,
    JourneyStage.POSTPARTUM: 0.5,
    JourneyStage.LACTATION: 0.4,
}

CONVERSION_AFFINITY: dict[TopicIntent, float] = {
    TopicIntent.ACT: 1.0,
    TopicIntent.DECIDE: 1.0,
    TopicIntent.MONITOR: 0.6,
    TopicIntent.LEARN: 0.3,
    TopicIntent.COPE: 0.2,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def monetization_potential(monetization_class: MonetizationClass) -> float:
    """Score the monetization potential of a topic's class."""
    return MONETIZATION_POTENTIAL.get(monetization_class, 0.0)


def competition_gap(serp_quality: float) -> float:
    """Opportunity = inverse of existing SERP quality (0-1 scale).

    Lower SERP quality means a bigger gap to fill.
    """
    clamped = max(0.0, min(serp_quality, 1.0))
    return 1.0 - clamped


def audience_match(journey_stage: JourneyStage) -> float:
    """Map journey stage to audience-value weight."""
    return AUDIENCE_MATCH.get(journey_stage, 0.3)


def conversion_affinity(intent: TopicIntent) -> float:
    """Map topic intent to conversion likelihood."""
    return CONVERSION_AFFINITY.get(intent, 0.2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_commercial_score(
    monetization_class: MonetizationClass,
    serp_quality: float,
    journey_stage: JourneyStage,
    intent: TopicIntent,
) -> float:
    """Compute a commercial fit score in [0, 100].

    Parameters
    ----------
    monetization_class:
        How the topic can be monetised.
    serp_quality:
        Quality of existing SERP results (0.0 = garbage, 1.0 = excellent).
    journey_stage:
        Where the user sits in their fertility journey.
    intent:
        The dominant user intent behind the topic.

    Returns
    -------
    float
        Commercial fit score clamped to [0, 100].
    """
    raw = (
        W_MONETIZATION * monetization_potential(monetization_class)
        + W_COMPETITION_GAP * competition_gap(serp_quality)
        + W_AUDIENCE_MATCH * audience_match(journey_stage)
        + W_CONVERSION * conversion_affinity(intent)
    ) * 100.0

    return max(0.0, min(raw, 100.0))
