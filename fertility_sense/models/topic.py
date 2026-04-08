"""Topic ontology models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JourneyStage(str, Enum):
    PRECONCEPTION = "preconception"
    TRYING = "trying"
    FERTILITY_TREATMENT = "fertility_treatment"
    PREGNANCY_T1 = "pregnancy_t1"
    PREGNANCY_T2 = "pregnancy_t2"
    PREGNANCY_T3 = "pregnancy_t3"
    LABOR_DELIVERY = "labor_delivery"
    POSTPARTUM = "postpartum"
    LACTATION = "lactation"


class TopicIntent(str, Enum):
    LEARN = "learn"       # Educational: "what is AMH?"
    DECIDE = "decide"     # Decision support: "IUI vs IVF?"
    ACT = "act"           # Action-oriented: "how to use OPK"
    MONITOR = "monitor"   # Tracking: "is this normal at 8 weeks?"
    COPE = "cope"         # Emotional: "dealing with TWW anxiety"


class RiskTier(str, Enum):
    GREEN = "green"    # General wellness, no clinical risk
    YELLOW = "yellow"  # Clinically adjacent, requires evidence backing
    RED = "red"        # Medical decision, requires high-grade evidence + escalation
    BLACK = "black"    # Disallowed: diagnosis, dosage, emergency triage


class MonetizationClass(str, Enum):
    CONTENT = "content"     # Article, guide, video
    TOOL = "tool"           # Calculator, tracker, quiz
    REFERRAL = "referral"   # Provider, product, service referral
    COMMERCE = "commerce"   # Affiliate, DTC product
    NONE = "none"           # Not monetizable


class TopicNode(BaseModel):
    topic_id: str = Field(description="Canonical slug: 'ovulation-tracking'")
    display_name: str
    aliases: list[str] = Field(default_factory=list)
    journey_stage: JourneyStage
    intent: TopicIntent
    risk_tier: RiskTier
    parent_id: Optional[str] = None
    children: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    monetization_class: MonetizationClass = MonetizationClass.CONTENT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Alias(BaseModel):
    surface_form: str = Field(description="Raw text as seen in signals")
    canonical_topic_id: str = Field(description="Resolved target topic_id")
    source: str = Field(description="Where the alias was discovered")
    confidence: float = Field(ge=0.0, le=1.0, description="Resolution confidence")
    created_at: datetime = Field(default_factory=datetime.utcnow)
