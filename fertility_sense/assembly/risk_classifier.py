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

# BLACK keywords — always escalate to BLACK regardless of topic
BLACK_ALWAYS = {
    "am i having a miscarriage",
    "is this an emergency",
    "should i go to the er",
    "diagnose",
    "can you tell me if i have",
}

# BLACK keywords that only apply to GREEN topics — on YELLOW/RED topics
# these are expected clinical questions that should stay at their tier
BLACK_ON_GREEN_ONLY = {
    "should i take",
    "how much",
    "what dose",
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

    Topic-aware BLACK keywords: "should I take" on a YELLOW prenatal-vitamins
    topic is a reasonable question (escalate to RED, not BLACK). On a GREEN
    fertility-diet topic, it's a dosage question (escalate to BLACK).
    """
    query_lower = query.lower()

    # Start with topic's intrinsic tier
    tier = topic.risk_tier

    # Always-BLACK keywords — regardless of topic tier
    if any(kw in query_lower for kw in BLACK_ALWAYS):
        return RiskTier.BLACK

    # Topic-aware BLACK: only escalate to BLACK on GREEN topics
    # On YELLOW/RED topics, these are expected questions → escalate to RED instead
    if any(kw in query_lower for kw in BLACK_ON_GREEN_ONLY):
        if tier == RiskTier.GREEN:
            return RiskTier.BLACK
        # For YELLOW/RED, escalate to RED (not BLACK)
        return RiskTier.RED

    # Check for RED keyword escalation
    if tier in (RiskTier.GREEN, RiskTier.YELLOW):
        if any(kw in query_lower for kw in RED_KEYWORDS):
            tier = RiskTier.RED

    # Critical safety alerts force at least RED
    if retrieval.has_critical_alerts and tier in (RiskTier.GREEN, RiskTier.YELLOW):
        tier = RiskTier.RED

    return tier
