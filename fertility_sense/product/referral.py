"""Provider and product referral logic."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReferralCard:
    referral_type: str  # "provider", "product", "service", "lab"
    title: str
    description: str
    eligibility_criteria: list[str] = field(default_factory=list)
    journey_stages: list[str] = field(default_factory=list)
    revenue_model: str = "referral_fee"


# Pre-defined referral templates
REFERRAL_TEMPLATES: list[ReferralCard] = [
    ReferralCard(
        referral_type="provider",
        title="Find a Reproductive Endocrinologist",
        description="Connect with board-certified REI specialists near you",
        eligibility_criteria=[
            "Trying to conceive for 12+ months (or 6+ months if age 35+)",
            "Known fertility diagnosis",
            "Considering IVF/IUI",
        ],
        journey_stages=["trying", "fertility_treatment"],
    ),
    ReferralCard(
        referral_type="lab",
        title="Fertility Bloodwork Panel",
        description="Order AMH, FSH, estradiol, and thyroid panel",
        eligibility_criteria=["Preconception planning", "Fertility evaluation"],
        journey_stages=["preconception", "trying"],
    ),
    ReferralCard(
        referral_type="product",
        title="Prenatal Vitamin Comparison",
        description="Compare evidence-backed prenatal vitamins",
        eligibility_criteria=["Planning pregnancy", "Currently pregnant"],
        journey_stages=["preconception", "trying", "pregnancy_t1", "pregnancy_t2", "pregnancy_t3"],
        revenue_model="affiliate",
    ),
    ReferralCard(
        referral_type="service",
        title="Genetic Counseling Referral",
        description="Connect with certified genetic counselors",
        eligibility_criteria=[
            "Carrier screening results",
            "Family history concerns",
            "Advanced maternal age",
        ],
        journey_stages=["preconception", "pregnancy_t1"],
        revenue_model="referral_fee",
    ),
]
