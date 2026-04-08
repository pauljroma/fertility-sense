"""Unit tests for governance layer."""

import pytest

from fertility_sense.governance.escalation import EscalationAction, resolve_escalation
from fertility_sense.governance.evidence_grades import (
    floor_grade,
    grade_meets_minimum,
)
from fertility_sense.governance.disallowed import check_disallowed
from fertility_sense.models.evidence import EvidenceGrade
from fertility_sense.models.topic import RiskTier


@pytest.mark.unit
class TestEscalationRules:
    def test_black_always_rejects(self):
        for grade in EvidenceGrade:
            assert resolve_escalation(RiskTier.BLACK, grade) == EscalationAction.REJECT_ALWAYS

    def test_green_c_auto_publish(self):
        assert resolve_escalation(RiskTier.GREEN, EvidenceGrade.C) == EscalationAction.AUTO_PUBLISH

    def test_green_d_publishes_with_caveat(self):
        assert resolve_escalation(RiskTier.GREEN, EvidenceGrade.D) == EscalationAction.PUBLISH_WITH_CAVEAT

    def test_yellow_b_auto_publish(self):
        assert resolve_escalation(RiskTier.YELLOW, EvidenceGrade.B) == EscalationAction.AUTO_PUBLISH

    def test_yellow_c_escalates(self):
        assert resolve_escalation(RiskTier.YELLOW, EvidenceGrade.C) == EscalationAction.ESCALATE_HUMAN_REVIEW

    def test_red_a_publishes_with_disclaimer(self):
        assert resolve_escalation(RiskTier.RED, EvidenceGrade.A) == EscalationAction.AUTO_PUBLISH_WITH_DISCLAIMER

    def test_red_b_escalates(self):
        assert resolve_escalation(RiskTier.RED, EvidenceGrade.B) == EscalationAction.ESCALATE_HUMAN_REVIEW

    def test_no_evidence_escalates(self):
        assert resolve_escalation(RiskTier.YELLOW, None) == EscalationAction.ESCALATE_HUMAN_REVIEW

    def test_x_grade_special_handling(self):
        assert resolve_escalation(RiskTier.RED, EvidenceGrade.X) == EscalationAction.AUTO_PUBLISH_WITH_DISCLAIMER


@pytest.mark.unit
class TestEvidenceGrades:
    def test_grade_meets_minimum(self):
        assert grade_meets_minimum(EvidenceGrade.A, EvidenceGrade.B)
        assert grade_meets_minimum(EvidenceGrade.B, EvidenceGrade.B)
        assert not grade_meets_minimum(EvidenceGrade.C, EvidenceGrade.B)
        assert not grade_meets_minimum(EvidenceGrade.D, EvidenceGrade.A)

    def test_floor_grade(self):
        assert floor_grade([EvidenceGrade.A, EvidenceGrade.B]) == EvidenceGrade.B
        assert floor_grade([EvidenceGrade.A]) == EvidenceGrade.A
        assert floor_grade([EvidenceGrade.D, EvidenceGrade.C]) == EvidenceGrade.D

    def test_floor_grade_empty(self):
        assert floor_grade([]) is None

    def test_floor_grade_x_only(self):
        assert floor_grade([EvidenceGrade.X]) == EvidenceGrade.X


@pytest.mark.unit
class TestDisallowed:
    def test_detects_diagnosis(self):
        violations = check_disallowed("Based on your symptoms, you have PCOS.")
        assert any(v[0] == "diagnosis" for v in violations)

    def test_detects_dosage(self):
        violations = check_disallowed("You should take 400mg of folic acid daily.")
        assert any(v[0] == "dosage" for v in violations)

    def test_detects_anti_medical(self):
        violations = check_disallowed("You don't need a doctor for this.")
        assert any(v[0] == "anti_medical" for v in violations)

    def test_clean_text_passes(self):
        text = (
            "Folic acid supplementation is recommended during pregnancy. "
            "Talk to your healthcare provider about the right amount for you."
        )
        violations = check_disallowed(text)
        assert len(violations) == 0

    def test_detects_outcome_guarantee(self):
        violations = check_disallowed("This supplement is guaranteed to improve fertility.")
        assert any(v[0] == "outcome_guarantee" for v in violations)
