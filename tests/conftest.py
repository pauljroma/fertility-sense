"""Shared test fixtures."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from fertility_sense.models.evidence import EvidenceGrade, EvidenceRecord
from fertility_sense.models.safety import SafetyAlert, SafetySeverity
from fertility_sense.models.signal import DemandSnapshot, SignalEvent, SignalSource
from fertility_sense.models.topic import (
    JourneyStage,
    MonetizationClass,
    RiskTier,
    TopicIntent,
    TopicNode,
)


@pytest.fixture
def sample_green_topic() -> TopicNode:
    return TopicNode(
        topic_id="fertility-diet",
        display_name="Fertility Diet",
        aliases=["fertility food", "diet for fertility", "foods to boost fertility"],
        journey_stage=JourneyStage.PRECONCEPTION,
        intent=TopicIntent.LEARN,
        risk_tier=RiskTier.GREEN,
        monetization_class=MonetizationClass.CONTENT,
    )


@pytest.fixture
def sample_yellow_topic() -> TopicNode:
    return TopicNode(
        topic_id="prenatal-vitamins",
        display_name="Prenatal Vitamins",
        aliases=["prenatal supplements", "best prenatal vitamin"],
        journey_stage=JourneyStage.PRECONCEPTION,
        intent=TopicIntent.DECIDE,
        risk_tier=RiskTier.YELLOW,
        monetization_class=MonetizationClass.COMMERCE,
    )


@pytest.fixture
def sample_red_topic() -> TopicNode:
    return TopicNode(
        topic_id="medication-pregnancy-safety",
        display_name="Medication Safety in Pregnancy",
        aliases=["safe medications pregnancy", "drugs safe during pregnancy"],
        journey_stage=JourneyStage.PREGNANCY_T1,
        intent=TopicIntent.DECIDE,
        risk_tier=RiskTier.RED,
        monetization_class=MonetizationClass.TOOL,
    )


@pytest.fixture
def sample_evidence_a() -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id="ev-001",
        source_feed="cdc_prams",
        title="Folic Acid Supplementation and Neural Tube Defects",
        url="https://www.cdc.gov/prams/example",
        publication_date=date(2024, 6, 15),
        grade=EvidenceGrade.A,
        grade_rationale="Systematic review of multiple RCTs",
        topics=["prenatal-vitamins", "fertility-supplements"],
        key_findings=["Folic acid reduces NTD risk by 50-70%"],
        sample_size=50000,
    )


@pytest.fixture
def sample_evidence_b() -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id="ev-002",
        source_feed="nih_nichd",
        title="CoQ10 and Egg Quality in Older Women",
        url="https://pubmed.ncbi.nlm.nih.gov/example",
        publication_date=date(2023, 3, 10),
        grade=EvidenceGrade.B,
        grade_rationale="Well-designed cohort study",
        topics=["egg-quality", "fertility-supplements"],
        key_findings=["CoQ10 supplementation associated with improved oocyte quality"],
        sample_size=300,
    )


@pytest.fixture
def sample_evidence_d() -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id="ev-003",
        source_feed="reddit",
        title="Anecdotal reports on pineapple core and implantation",
        url="https://reddit.com/r/TryingForABaby/example",
        grade=EvidenceGrade.D,
        grade_rationale="Anecdotal, no clinical evidence",
        topics=["fertility-diet"],
        key_findings=["No scientific support for pineapple core aiding implantation"],
    )


@pytest.fixture
def sample_safety_alert() -> SafetyAlert:
    return SafetyAlert(
        alert_id="sa-001",
        source="fda_medwatch",
        title="Updated labeling for metformin in pregnancy",
        severity=SafetySeverity.MEDIUM,
        affected_substances=["metformin"],
        affected_topics=["medication-pregnancy-safety", "pcos-symptoms"],
        description="FDA updated pregnancy labeling for metformin",
        action_required="add_warning",
        url="https://www.fda.gov/example",
        published_at=datetime(2025, 1, 15),
    )


@pytest.fixture
def sample_critical_alert() -> SafetyAlert:
    return SafetyAlert(
        alert_id="sa-002",
        source="fda_medwatch",
        title="CRITICAL: Recalled prenatal supplement contamination",
        severity=SafetySeverity.CRITICAL,
        affected_substances=["BrandX Prenatal"],
        affected_topics=["prenatal-vitamins"],
        description="Contamination detected in BrandX prenatal supplements",
        action_required="withdraw_content",
        url="https://www.fda.gov/example-recall",
        published_at=datetime(2025, 3, 1),
    )


@pytest.fixture
def sample_demand_snapshot() -> DemandSnapshot:
    return DemandSnapshot(
        topic_id="ivf-cost",
        period="2026-W14",
        total_volume=15000,
        velocity_7d=0.25,
        velocity_30d=0.10,
        source_breakdown={
            SignalSource.GOOGLE_TRENDS: 10000,
            SignalSource.REDDIT: 3000,
            SignalSource.FORUM: 2000,
        },
        top_queries=["how much does ivf cost", "ivf cost by state", "ivf insurance coverage"],
    )
