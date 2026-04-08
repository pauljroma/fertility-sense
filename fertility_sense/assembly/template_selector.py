"""Answer template selection based on risk tier and intent."""

from __future__ import annotations

from fertility_sense.models.answer import AnswerTemplate
from fertility_sense.models.evidence import EvidenceGrade
from fertility_sense.models.topic import RiskTier, TopicIntent

# Built-in answer templates
TEMPLATES: list[AnswerTemplate] = [
    # GREEN templates
    AnswerTemplate(
        template_id="green-learn",
        name="Green Educational",
        risk_tier=RiskTier.GREEN,
        intent=TopicIntent.LEARN,
        structure=["summary", "key_facts", "tips", "sources"],
        required_evidence_grade=EvidenceGrade.D,
        requires_human_review=False,
    ),
    AnswerTemplate(
        template_id="green-decide",
        name="Green Decision Support",
        risk_tier=RiskTier.GREEN,
        intent=TopicIntent.DECIDE,
        structure=["summary", "options", "considerations", "sources"],
        required_evidence_grade=EvidenceGrade.C,
        requires_human_review=False,
    ),
    # YELLOW templates
    AnswerTemplate(
        template_id="yellow-learn",
        name="Yellow Educational",
        risk_tier=RiskTier.YELLOW,
        intent=TopicIntent.LEARN,
        structure=["summary", "evidence", "what_to_know", "when_to_see_doctor", "sources"],
        required_evidence_grade=EvidenceGrade.B,
        requires_human_review=False,
    ),
    AnswerTemplate(
        template_id="yellow-decide",
        name="Yellow Decision Support",
        risk_tier=RiskTier.YELLOW,
        intent=TopicIntent.DECIDE,
        structure=[
            "summary", "evidence_for", "evidence_against",
            "expert_recommendation", "when_to_see_doctor", "sources",
        ],
        required_evidence_grade=EvidenceGrade.B,
        requires_human_review=False,
    ),
    # RED templates
    AnswerTemplate(
        template_id="red-learn",
        name="Red Clinical Educational",
        risk_tier=RiskTier.RED,
        intent=TopicIntent.LEARN,
        structure=[
            "clinical_summary", "evidence", "important_disclaimer",
            "consult_provider", "sources",
        ],
        required_evidence_grade=EvidenceGrade.A,
        requires_human_review=True,
    ),
    AnswerTemplate(
        template_id="red-decide",
        name="Red Clinical Decision Support",
        risk_tier=RiskTier.RED,
        intent=TopicIntent.DECIDE,
        structure=[
            "clinical_summary", "evidence", "risk_benefit",
            "important_disclaimer", "consult_provider", "sources",
        ],
        required_evidence_grade=EvidenceGrade.A,
        requires_human_review=True,
    ),
    # BLACK template
    AnswerTemplate(
        template_id="black-escalation",
        name="Black Escalation Only",
        risk_tier=RiskTier.BLACK,
        intent=TopicIntent.LEARN,
        structure=["escalation_message"],
        required_evidence_grade=EvidenceGrade.A,
        requires_human_review=False,
        escalation_text=(
            "This question requires personalized medical guidance. "
            "Please consult your healthcare provider or call your clinic directly. "
            "If you are experiencing an emergency, call 911 or go to your nearest ER."
        ),
    ),
    # COPE templates (any risk tier)
    AnswerTemplate(
        template_id="green-cope",
        name="Emotional Support",
        risk_tier=RiskTier.GREEN,
        intent=TopicIntent.COPE,
        structure=["validation", "what_others_experience", "coping_strategies", "resources"],
        required_evidence_grade=EvidenceGrade.D,
        requires_human_review=False,
    ),
]

_TEMPLATE_INDEX: dict[tuple[RiskTier, TopicIntent], AnswerTemplate] | None = None


def _build_index() -> dict[tuple[RiskTier, TopicIntent], AnswerTemplate]:
    global _TEMPLATE_INDEX
    if _TEMPLATE_INDEX is None:
        _TEMPLATE_INDEX = {(t.risk_tier, t.intent): t for t in TEMPLATES}
    return _TEMPLATE_INDEX


def select_template(risk_tier: RiskTier, intent: TopicIntent) -> AnswerTemplate:
    """Select the best answer template for a given risk tier and intent.

    Falls back to LEARN intent if exact match not found.
    BLACK tier always returns the escalation template.
    """
    if risk_tier == RiskTier.BLACK:
        return next(t for t in TEMPLATES if t.template_id == "black-escalation")

    index = _build_index()
    template = index.get((risk_tier, intent))
    if template:
        return template

    # Fallback to LEARN intent for this risk tier
    template = index.get((risk_tier, TopicIntent.LEARN))
    if template:
        return template

    # Last resort: GREEN LEARN
    return index[(RiskTier.GREEN, TopicIntent.LEARN)]
