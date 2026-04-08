"""Content brief generation from demand signals."""

from __future__ import annotations

import uuid
from datetime import datetime

from fertility_sense.models.product import ContentBrief
from fertility_sense.models.scoring import TopicOpportunityScore
from fertility_sense.models.topic import TopicNode


def generate_content_brief(
    topic: TopicNode,
    score: TopicOpportunityScore,
) -> ContentBrief:
    """Generate a content brief for a high-scoring topic."""
    return ContentBrief(
        brief_id=str(uuid.uuid4()),
        topic_id=topic.topic_id,
        title=f"What to Know About {topic.display_name}",
        angle=_suggest_angle(topic, score),
        target_length_words=_target_length(topic),
        evidence_requirements=_evidence_requirements(topic),
        target_audience=_target_audience(topic),
        journey_stage=topic.journey_stage.value,
        seo_keywords=[topic.display_name] + topic.aliases[:5],
        created_at=datetime.utcnow(),
    )


def _suggest_angle(topic: TopicNode, score: TopicOpportunityScore) -> str:
    if score.demand_score > 70:
        return f"Trending topic: high consumer demand for {topic.display_name}"
    if score.clinical_importance > 70:
        return f"Clinically important: evidence-backed guide to {topic.display_name}"
    return f"Comprehensive guide to {topic.display_name}"


def _target_length(topic: TopicNode) -> int:
    from fertility_sense.models.topic import RiskTier

    if topic.risk_tier in (RiskTier.RED, RiskTier.BLACK):
        return 2000  # Longer for clinical topics
    return 1200


def _evidence_requirements(topic: TopicNode) -> list[str]:
    from fertility_sense.models.topic import RiskTier

    reqs = ["At least 2 evidence records required"]
    if topic.risk_tier == RiskTier.RED:
        reqs.append("Grade A evidence required")
    elif topic.risk_tier == RiskTier.YELLOW:
        reqs.append("Grade B or higher evidence required")
    return reqs


def _target_audience(topic: TopicNode) -> str:
    stage_audiences = {
        "preconception": "Women planning pregnancy",
        "trying": "Couples actively trying to conceive",
        "fertility_treatment": "Patients undergoing fertility treatment",
        "pregnancy_t1": "Women in first trimester",
        "pregnancy_t2": "Women in second trimester",
        "pregnancy_t3": "Women in third trimester",
        "postpartum": "New mothers",
        "lactation": "Breastfeeding mothers",
    }
    return stage_audiences.get(topic.journey_stage.value, "General fertility audience")
