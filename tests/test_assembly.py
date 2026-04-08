"""Unit tests for answer assembly pipeline."""

import pytest

from fertility_sense.assembly.retriever import EvidenceRetriever, RetrievalResult
from fertility_sense.assembly.risk_classifier import classify_risk
from fertility_sense.assembly.template_selector import select_template
from fertility_sense.assembly.governor import run_governance_gate, build_provenance
from fertility_sense.assembly.assembler import AnswerAssembler
from fertility_sense.models.evidence import EvidenceGrade
from fertility_sense.models.topic import RiskTier, TopicIntent


@pytest.mark.unit
def test_retriever_finds_evidence(sample_green_topic, sample_evidence_d):
    retriever = EvidenceRetriever(
        evidence_records=[sample_evidence_d],
        safety_alerts=[],
    )
    result = retriever.retrieve("fertility-diet")
    assert result.has_evidence
    assert len(result.evidence) == 1


@pytest.mark.unit
def test_retriever_empty(sample_green_topic):
    retriever = EvidenceRetriever(evidence_records=[], safety_alerts=[])
    result = retriever.retrieve("fertility-diet")
    assert not result.has_evidence
    assert result.best_grade is None


@pytest.mark.unit
def test_risk_classifier_green_stays_green(sample_green_topic):
    retrieval = RetrievalResult(topic_id="fertility-diet")
    tier = classify_risk(sample_green_topic, "what foods help fertility", retrieval)
    assert tier == RiskTier.GREEN


@pytest.mark.unit
def test_risk_classifier_escalates_to_black(sample_green_topic):
    retrieval = RetrievalResult(topic_id="fertility-diet")
    tier = classify_risk(sample_green_topic, "can you tell me if i have PCOS", retrieval)
    assert tier == RiskTier.BLACK


@pytest.mark.unit
def test_risk_classifier_escalates_on_medication(sample_green_topic):
    retrieval = RetrievalResult(topic_id="fertility-diet")
    tier = classify_risk(sample_green_topic, "is this medication safe during pregnancy", retrieval)
    assert tier == RiskTier.RED


@pytest.mark.unit
def test_risk_classifier_critical_alert_escalates(sample_yellow_topic, sample_critical_alert):
    retrieval = RetrievalResult(
        topic_id="prenatal-vitamins",
        safety_alerts=[sample_critical_alert],
    )
    tier = classify_risk(sample_yellow_topic, "best prenatal vitamins", retrieval)
    assert tier == RiskTier.RED


@pytest.mark.unit
def test_template_selector_green_learn():
    template = select_template(RiskTier.GREEN, TopicIntent.LEARN)
    assert template.template_id == "green-learn"
    assert "summary" in template.structure


@pytest.mark.unit
def test_template_selector_black():
    template = select_template(RiskTier.BLACK, TopicIntent.LEARN)
    assert template.template_id == "black-escalation"
    assert template.escalation_text is not None


@pytest.mark.unit
def test_template_selector_fallback():
    # MONITOR intent falls back to LEARN
    template = select_template(RiskTier.GREEN, TopicIntent.MONITOR)
    assert template.risk_tier == RiskTier.GREEN


@pytest.mark.unit
def test_governance_gate_green_passes(sample_evidence_d):
    from fertility_sense.assembly.template_selector import select_template

    template = select_template(RiskTier.GREEN, TopicIntent.LEARN)
    retrieval = RetrievalResult(
        topic_id="fertility-diet",
        evidence=[sample_evidence_d],
    )
    result = run_governance_gate(
        {"summary": "Healthy eating can support fertility."},
        template,
        retrieval,
        RiskTier.GREEN,
    )
    assert result.passed or result.status == "pending_review"


@pytest.mark.unit
def test_governance_gate_blocks_disallowed(sample_evidence_a):
    from fertility_sense.assembly.template_selector import select_template

    template = select_template(RiskTier.YELLOW, TopicIntent.LEARN)
    retrieval = RetrievalResult(
        topic_id="prenatal-vitamins",
        evidence=[sample_evidence_a],
    )
    result = run_governance_gate(
        {"summary": "You should take 400mg daily."},
        template,
        retrieval,
        RiskTier.YELLOW,
    )
    assert not result.passed  # Dosage is disallowed


@pytest.mark.unit
def test_full_assembly_green(sample_green_topic, sample_evidence_d):
    retriever = EvidenceRetriever(
        evidence_records=[sample_evidence_d],
        safety_alerts=[],
    )
    assembler = AnswerAssembler(retriever)
    answer = assembler.assemble(sample_green_topic, "what foods help with fertility")
    assert answer.topic_id == "fertility-diet"
    assert answer.risk_tier == RiskTier.GREEN
    assert answer.provenance is not None


@pytest.mark.unit
def test_full_assembly_black_query(sample_green_topic):
    retriever = EvidenceRetriever(evidence_records=[], safety_alerts=[])
    assembler = AnswerAssembler(retriever)
    answer = assembler.assemble(sample_green_topic, "am i having a miscarriage")
    assert answer.risk_tier == RiskTier.BLACK
    assert "escalation_message" in answer.sections
