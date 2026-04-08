"""Commerce opportunity identification."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CommerceOpportunity:
    category: str
    product_type: str
    revenue_model: str  # "affiliate", "dtc", "subscription", "referral_fee"
    estimated_aov: float  # Average order value
    journey_stages: list[str] = field(default_factory=list)
    notes: str = ""


COMMERCE_MAP: list[CommerceOpportunity] = [
    CommerceOpportunity(
        category="supplements",
        product_type="Prenatal vitamins",
        revenue_model="affiliate",
        estimated_aov=35.0,
        journey_stages=["preconception", "trying", "pregnancy_t1", "pregnancy_t2", "pregnancy_t3"],
        notes="High volume, recurring purchase. CoQ10, folate, DHA are top sellers.",
    ),
    CommerceOpportunity(
        category="diagnostics",
        product_type="Ovulation prediction kits",
        revenue_model="affiliate",
        estimated_aov=30.0,
        journey_stages=["trying"],
        notes="High intent, repeat purchase during TTC phase.",
    ),
    CommerceOpportunity(
        category="diagnostics",
        product_type="At-home fertility tests",
        revenue_model="affiliate",
        estimated_aov=150.0,
        journey_stages=["preconception", "trying"],
        notes="AMH, sperm analysis kits. Growing DTC market.",
    ),
    CommerceOpportunity(
        category="services",
        product_type="Telehealth fertility consults",
        revenue_model="referral_fee",
        estimated_aov=200.0,
        journey_stages=["trying", "fertility_treatment"],
        notes="High conversion for users with clinical questions.",
    ),
    CommerceOpportunity(
        category="education",
        product_type="Fertility courses / coaching",
        revenue_model="subscription",
        estimated_aov=99.0,
        journey_stages=["trying", "fertility_treatment"],
    ),
    CommerceOpportunity(
        category="wearables",
        product_type="Fertility trackers / wearables",
        revenue_model="affiliate",
        estimated_aov=250.0,
        journey_stages=["trying", "preconception"],
        notes="Tempdrop, Oura, Ava — high AOV.",
    ),
]
