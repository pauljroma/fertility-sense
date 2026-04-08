"""Demand scoring: quantifies topic demand from volume, velocity, breadth, and recency."""

from __future__ import annotations

import math

from fertility_sense.models.signal import DemandSnapshot

# ---------------------------------------------------------------------------
# Weights
# ---------------------------------------------------------------------------
W_VOLUME = 0.35
W_VELOCITY = 0.30
W_BREADTH = 0.20
W_RECENCY = 0.15


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def normalized_volume(volume: int, p95_volume: int) -> float:
    """Scale volume to [0, 1] using the p95 ceiling.

    Values at or above p95 are capped to 1.0.
    """
    if p95_volume <= 0:
        return 0.0
    return min(volume / p95_volume, 1.0)


def sigmoid(x: float, midpoint: float = 0.15, steepness: float = 20.0) -> float:
    """Standard logistic sigmoid mapped to [0, 1].

    ``sigmoid(midpoint) ≈ 0.5`` by construction.
    """
    z = steepness * (x - midpoint)
    # Clamp to avoid overflow in math.exp
    z = max(min(z, 500.0), -500.0)
    return 1.0 / (1.0 + math.exp(-z))


def velocity_score(velocity_7d: float) -> float:
    """Score velocity through a sigmoid centered at 15 % week-over-week growth."""
    return sigmoid(velocity_7d, midpoint=0.15, steepness=20.0)


def breadth_score(source_count: int, total_sources: int) -> float:
    """Fraction of active sources that surfaced the topic."""
    if total_sources <= 0:
        return 0.0
    return source_count / total_sources


def recency_bonus(hours_since_first: float) -> float:
    """Exponential decay with a 7-day (168-hour) half-life.

    A brand-new signal (hours=0) scores 1.0; after one week it drops to ~0.37.
    """
    if hours_since_first < 0:
        hours_since_first = 0.0
    return math.exp(-hours_since_first / 168.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_demand_score(
    snapshot: DemandSnapshot,
    p95_volume: int,
    total_sources: int,
    hours_since_first: float,
) -> float:
    """Compute a demand score in [0, 100].

    Parameters
    ----------
    snapshot:
        Aggregated demand snapshot for a topic/period.
    p95_volume:
        95th-percentile volume across all topics in the same period.
        Used to normalise the raw volume.
    total_sources:
        Number of distinct signal sources active in this period.
    hours_since_first:
        Hours elapsed since the *first* signal for this topic was observed.

    Returns
    -------
    float
        Demand score clamped to [0, 100].
    """
    source_count = len(snapshot.source_breakdown)

    raw = (
        W_VOLUME * normalized_volume(snapshot.total_volume, p95_volume)
        + W_VELOCITY * velocity_score(snapshot.velocity_7d)
        + W_BREADTH * breadth_score(source_count, total_sources)
        + W_RECENCY * recency_bonus(hours_since_first)
    ) * 100.0

    return max(0.0, min(raw, 100.0))
