"""Risk tier classification for topic + query combinations."""

from __future__ import annotations

from fertility_sense.assembly.retriever import RetrievalResult
from fertility_sense.models.topic import RiskTier, TopicNode


# Keywords that escalate risk tier
RED_KEYWORDS = {
    "medication", "drug", "dose", "dosage", "prescri", "safe to take",
    "contraindicated", "teratogen", "exposure", "radiation", "x-ray",
    "miscarriage", "ectopic", "molar", "hemorrhage", "preeclampsia",
    "placenta previa", "preterm labor", "emergency", "bleeding",
}

BLACK_KEYWORDS = {
    "should i take", "how much", "what dose", "am i having a miscarriage",
    "is this an emergency", "should i go to the er", "diagnose",
    "can you tell me if i have",
}


def classify_risk(
    topic: TopicNode,
    query: str,
    retrieval: RetrievalResult,
) -> RiskTier:
    """Classify the effective risk tier for a topic + query.

    The effective risk tier is the maximum of:
    1. The topic's intrinsic risk tier
    2. Risk escalation from query keywords
    3. Risk escalation from active safety alerts
    """
    query_lower = query.lower()

    # Start with topic's intrinsic tier
    tier = topic.risk_tier

    # Check for BLACK keyword escalation
    if any(kw in query_lower for kw in BLACK_KEYWORDS):
        return RiskTier.BLACK

    # Check for RED keyword escalation
    if tier in (RiskTier.GREEN, RiskTier.YELLOW):
        if any(kw in query_lower for kw in RED_KEYWORDS):
            tier = RiskTier.RED

    # Critical safety alerts force at least RED
    if retrieval.has_critical_alerts and tier in (RiskTier.GREEN, RiskTier.YELLOW):
        tier = RiskTier.RED

    return tier
