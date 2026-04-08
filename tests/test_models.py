"""Unit tests for Pydantic models."""

import pytest
from datetime import date, datetime

from fertility_sense.models.topic import (
    TopicNode, Alias, JourneyStage, TopicIntent, RiskTier, MonetizationClass,
)
from fertility_sense.models.signal import SignalEvent, SignalSource, DemandSnapshot
from fertility_sense.models.evidence import EvidenceRecord, EvidenceGrade
from fertility_sense.models.safety import SafetyAlert, SafetySeverity
from fertility_sense.models.scoring import TopicOpportunityScore
from fertility_sense.models.answer import GovernedAnswer, Provenance, AnswerTemplate
from fertility_sense.models.interaction import UserInteraction
from fertility_sense.models.clinic import ClinicRecord
from fertility_sense.models.product import ProductOption, ProductType


@pytest.mark.unit
def test_topic_node_creation(sample_green_topic):
    assert sample_green_topic.topic_id == "fertility-diet"
    assert sample_green_topic.risk_tier == RiskTier.GREEN
    assert sample_green_topic.journey_stage == JourneyStage.PRECONCEPTION


@pytest.mark.unit
def test_topic_node_serialization(sample_green_topic):
    data = sample_green_topic.model_dump()
    restored = TopicNode.model_validate(data)
    assert restored.topic_id == sample_green_topic.topic_id


@pytest.mark.unit
def test_alias_validation():
    alias = Alias(
        surface_form="OPK",
        canonical_topic_id="opk-testing",
        source="seed",
        confidence=0.95,
    )
    assert alias.confidence == 0.95


@pytest.mark.unit
def test_alias_confidence_bounds():
    with pytest.raises(Exception):
        Alias(
            surface_form="test",
            canonical_topic_id="test",
            source="test",
            confidence=1.5,  # > 1.0
        )


@pytest.mark.unit
def test_signal_event_creation():
    event = SignalEvent(
        signal_id="sig-001",
        source=SignalSource.GOOGLE_TRENDS,
        raw_query="ivf cost",
        volume=5000,
        velocity=0.15,
        observed_at=datetime.utcnow(),
    )
    assert event.source == SignalSource.GOOGLE_TRENDS
    assert event.geo == "US"


@pytest.mark.unit
def test_evidence_record_grades(sample_evidence_a, sample_evidence_b):
    assert sample_evidence_a.grade == EvidenceGrade.A
    assert sample_evidence_b.grade == EvidenceGrade.B
    assert sample_evidence_a.sample_size == 50000


@pytest.mark.unit
def test_safety_alert_severity(sample_safety_alert, sample_critical_alert):
    assert sample_safety_alert.severity == SafetySeverity.MEDIUM
    assert sample_critical_alert.severity == SafetySeverity.CRITICAL
    assert not sample_critical_alert.resolved


@pytest.mark.unit
def test_tos_score_bounds():
    tos = TopicOpportunityScore(
        topic_id="test",
        period="2026-W14",
        demand_score=75.0,
        clinical_importance=60.0,
        trust_risk_score=80.0,
        commercial_fit=50.0,
        composite_tos=67.5,
    )
    assert 0 <= tos.composite_tos <= 100


@pytest.mark.unit
def test_tos_score_validation():
    with pytest.raises(Exception):
        TopicOpportunityScore(
            topic_id="test",
            period="2026-W14",
            demand_score=150.0,  # > 100
            clinical_importance=60.0,
            trust_risk_score=80.0,
            commercial_fit=50.0,
            composite_tos=67.5,
        )


@pytest.mark.unit
def test_product_option():
    opt = ProductOption(
        option_id="po-001",
        product_type=ProductType.TOOL,
        topic_id="ovulation-tracking",
        title="Ovulation Calculator",
        description="Predict fertile window",
        estimated_impact=0.7,
        estimated_effort="medium",
        priority_score=75.0,
    )
    assert opt.status == "proposed"
