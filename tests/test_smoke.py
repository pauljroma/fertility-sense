"""Smoke tests — 5 tests, <200ms total. Pre-commit gate."""

import pytest


@pytest.mark.smoke
def test_import_package():
    """Package imports without error."""
    import fertility_sense

    assert fertility_sense.__version__ == "0.1.0"


@pytest.mark.smoke
def test_import_models():
    """All model modules import cleanly."""
    from fertility_sense.models.topic import TopicNode, RiskTier, JourneyStage
    from fertility_sense.models.signal import SignalEvent
    from fertility_sense.models.evidence import EvidenceRecord, EvidenceGrade
    from fertility_sense.models.safety import SafetyAlert
    from fertility_sense.models.scoring import TopicOpportunityScore

    assert RiskTier.GREEN.value == "green"
    assert EvidenceGrade.A.value == "A"


@pytest.mark.smoke
def test_import_agents():
    """Agent registry loads."""
    from fertility_sense.nemoclaw.agents import ALL_AGENTS, AGENT_MAP

    assert len(ALL_AGENTS) == 11
    assert "demand-scout" in AGENT_MAP
    assert "answer-assembler" in AGENT_MAP
    assert "rfp-responder" in AGENT_MAP
    assert "competitive-intel" in AGENT_MAP
    assert "deal-manager" in AGENT_MAP


@pytest.mark.smoke
def test_governance_escalation():
    """Basic escalation rules work."""
    from fertility_sense.governance.escalation import EscalationAction, resolve_escalation
    from fertility_sense.models.evidence import EvidenceGrade
    from fertility_sense.models.topic import RiskTier

    assert resolve_escalation(RiskTier.BLACK, EvidenceGrade.A) == EscalationAction.REJECT_ALWAYS
    assert resolve_escalation(RiskTier.GREEN, EvidenceGrade.B) == EscalationAction.AUTO_PUBLISH


@pytest.mark.smoke
def test_config_defaults():
    """Config creates with sensible defaults."""
    from fertility_sense.config import FertilitySenseConfig

    config = FertilitySenseConfig()
    assert config.w_demand == 0.30
    assert config.trust_block_threshold == 20.0
