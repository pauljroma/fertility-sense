"""Unit tests for scoring engine."""

import pytest
from datetime import date, datetime

from fertility_sense.models.evidence import EvidenceGrade, EvidenceRecord
from fertility_sense.models.safety import SafetyAlert, SafetySeverity
from fertility_sense.models.signal import DemandSnapshot, SignalSource
from fertility_sense.models.topic import (
    JourneyStage, MonetizationClass, RiskTier, TopicIntent,
)
from fertility_sense.scoring.demand import compute_demand_score
from fertility_sense.scoring.clinical import compute_clinical_score
from fertility_sense.scoring.trust import compute_trust_score
from fertility_sense.scoring.commercial import compute_commercial_score
from fertility_sense.scoring.composite import compute_composite_tos


@pytest.mark.unit
def test_demand_score_basic(sample_demand_snapshot):
    score = compute_demand_score(
        snapshot=sample_demand_snapshot,
        p95_volume=20000,
        total_sources=5,
        hours_since_first=48.0,
    )
    assert 0 <= score <= 100


@pytest.mark.unit
def test_demand_score_zero_volume():
    snapshot = DemandSnapshot(
        topic_id="test",
        period="2026-W14",
        total_volume=0,
        velocity_7d=0.0,
        velocity_30d=0.0,
    )
    score = compute_demand_score(snapshot, p95_volume=20000, total_sources=5, hours_since_first=168.0)
    assert score < 20  # Low score for zero volume


@pytest.mark.unit
def test_demand_score_high_velocity(sample_demand_snapshot):
    sample_demand_snapshot.velocity_7d = 0.5  # 50% growth
    score = compute_demand_score(sample_demand_snapshot, p95_volume=20000, total_sources=5, hours_since_first=12.0)
    assert score > 50  # High velocity + recency should score well


@pytest.mark.unit
def test_clinical_score_with_evidence(sample_evidence_a, sample_evidence_b):
    score = compute_clinical_score(
        records=[sample_evidence_a, sample_evidence_b],
        risk_tier=RiskTier.YELLOW,
        prevalence_pct=0.05,
    )
    assert 0 <= score <= 100
    assert score > 30  # Should be moderate with grade A+B evidence


@pytest.mark.unit
def test_clinical_score_no_evidence():
    score = compute_clinical_score(
        records=[],
        risk_tier=RiskTier.GREEN,
        prevalence_pct=0.01,
    )
    assert score < 30  # Low without evidence


@pytest.mark.unit
def test_clinical_score_red_tier_boost(sample_evidence_a):
    green_score = compute_clinical_score([sample_evidence_a], RiskTier.GREEN, 0.05)
    red_score = compute_clinical_score([sample_evidence_a], RiskTier.RED, 0.05)
    assert red_score > green_score  # RED tier should score higher


@pytest.mark.unit
def test_trust_score_basic():
    score = compute_trust_score(
        min_evidence_grade=EvidenceGrade.A,
        active_alerts=[],
        risk_tier=RiskTier.GREEN,
        sources_agree=True,
        has_template=True,
        human_reviewed=True,
    )
    assert score > 80  # High trust with grade A, no alerts


@pytest.mark.unit
def test_trust_score_black_tier():
    score = compute_trust_score(
        min_evidence_grade=EvidenceGrade.A,
        active_alerts=[],
        risk_tier=RiskTier.BLACK,
        sources_agree=True,
        has_template=True,
        human_reviewed=True,
    )
    assert score == 0  # BLACK tier forces 0


@pytest.mark.unit
def test_trust_score_critical_alert(sample_critical_alert):
    score = compute_trust_score(
        min_evidence_grade=EvidenceGrade.A,
        active_alerts=[sample_critical_alert],
        risk_tier=RiskTier.YELLOW,
        sources_agree=True,
        has_template=True,
        human_reviewed=True,
    )
    assert score <= 20  # Capped at 20 with CRITICAL alert


@pytest.mark.unit
def test_commercial_score_high_value():
    score = compute_commercial_score(
        monetization_class=MonetizationClass.COMMERCE,
        serp_quality=0.2,  # Low competition
        journey_stage=JourneyStage.TRYING,
        intent=TopicIntent.ACT,
    )
    assert score > 70  # High value combination


@pytest.mark.unit
def test_commercial_score_low_value():
    score = compute_commercial_score(
        monetization_class=MonetizationClass.NONE,
        serp_quality=0.9,  # High competition
        journey_stage=JourneyStage.POSTPARTUM,
        intent=TopicIntent.COPE,
    )
    assert score < 30  # Low value combination


@pytest.mark.unit
def test_composite_tos_basic():
    tos = compute_composite_tos(
        topic_id="test",
        period="2026-W14",
        demand_score=70.0,
        clinical_importance=60.0,
        trust_risk_score=80.0,
        commercial_fit=50.0,
    )
    assert 0 <= tos.composite_tos <= 100
    assert not tos.unsafe_to_serve
    assert not tos.escalate_to_human


@pytest.mark.unit
def test_composite_tos_unsafe():
    tos = compute_composite_tos(
        topic_id="test",
        period="2026-W14",
        demand_score=90.0,
        clinical_importance=90.0,
        trust_risk_score=15.0,  # Below 20 threshold
        commercial_fit=80.0,
    )
    assert tos.unsafe_to_serve


@pytest.mark.unit
def test_composite_tos_escalation():
    tos = compute_composite_tos(
        topic_id="test",
        period="2026-W14",
        demand_score=50.0,
        clinical_importance=85.0,  # > 80
        trust_risk_score=35.0,   # < 40
        commercial_fit=50.0,
    )
    assert tos.escalate_to_human
