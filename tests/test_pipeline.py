"""End-to-end pipeline tests — verifies the full data path works."""

import pytest

from fertility_sense.config import FertilitySenseConfig
from fertility_sense.models.topic import RiskTier


@pytest.fixture
def pipeline():
    """Create a Pipeline instance with default config."""
    from fertility_sense.pipeline import Pipeline

    return Pipeline(FertilitySenseConfig())


@pytest.mark.unit
class TestPipelineInit:
    def test_loads_ontology(self, pipeline):
        assert len(pipeline.graph) > 10

    def test_loads_seed_evidence(self, pipeline):
        records = pipeline.evidence_store.all_records()
        assert len(records) >= 5, f"Expected 5+ seed records, got {len(records)}"

    def test_registers_feeds(self, pipeline):
        assert len(pipeline.registry) >= 1  # At least MotherToBaby

    def test_health_returns_data(self, pipeline):
        health = pipeline.health()
        assert health["topics"] > 0
        assert health["evidence_records"] > 0
        assert health["feeds"] >= 1


@pytest.mark.unit
class TestPipelineScore:
    def test_score_all_returns_ranked_list(self, pipeline):
        scores = pipeline.score(top_n=10)
        assert len(scores) > 0
        assert len(scores) <= 10
        # Should be sorted descending
        for i in range(len(scores) - 1):
            assert scores[i].composite_tos >= scores[i + 1].composite_tos

    def test_score_all_has_ranks(self, pipeline):
        scores = pipeline.score(top_n=5)
        assert scores[0].rank == 1
        assert scores[-1].rank == len(scores)

    def test_score_single_topic(self, pipeline):
        # Find a topic that has seed evidence
        all_records = pipeline.evidence_store.all_records()
        if not all_records:
            pytest.skip("No seed evidence loaded")
        topic_id = all_records[0].topics[0]
        scores = pipeline.score(topic_id=topic_id)
        assert len(scores) == 1
        assert scores[0].topic_id == topic_id
        assert 0 <= scores[0].composite_tos <= 100

    def test_score_nonexistent_topic(self, pipeline):
        scores = pipeline.score(topic_id="nonexistent-topic-xyz")
        assert scores == []

    def test_scores_have_valid_ranges(self, pipeline):
        scores = pipeline.score(top_n=5)
        for s in scores:
            assert 0 <= s.demand_score <= 100
            assert 0 <= s.clinical_importance <= 100
            assert 0 <= s.trust_risk_score <= 100
            assert 0 <= s.commercial_fit <= 100
            assert 0 <= s.composite_tos <= 100


@pytest.mark.unit
class TestPipelineAnswer:
    def test_answer_with_evidence(self, pipeline):
        # Find a topic with seed evidence
        all_records = pipeline.evidence_store.all_records()
        if not all_records:
            pytest.skip("No seed evidence loaded")
        topic_id = all_records[0].topics[0]
        result = pipeline.answer(topic_id, f"tell me about {topic_id}")
        assert result.topic_id == topic_id
        assert result.provenance is not None
        assert len(result.provenance.evidence_ids) > 0
        assert result.governance_status in ("published", "pending_review", "escalated")

    def test_answer_has_sections(self, pipeline):
        all_records = pipeline.evidence_store.all_records()
        if not all_records:
            pytest.skip("No seed evidence loaded")
        topic_id = all_records[0].topics[0]
        result = pipeline.answer(topic_id, "what should I know")
        assert len(result.sections) > 0

    def test_answer_nonexistent_topic_raises(self, pipeline):
        with pytest.raises(ValueError, match="not found"):
            pipeline.answer("nonexistent-topic-xyz", "test query")

    def test_answer_black_query_escalates(self, pipeline):
        all_records = pipeline.evidence_store.all_records()
        if not all_records:
            pytest.skip("No seed evidence loaded")
        topic_id = all_records[0].topics[0]
        # BLACK keywords trigger escalation
        result = pipeline.answer(topic_id, "am i having a miscarriage")
        assert result.risk_tier == RiskTier.BLACK
        assert "escalation_message" in result.sections


@pytest.mark.unit
class TestPipelineHealth:
    def test_health_structure(self, pipeline):
        health = pipeline.health()
        assert "topics" in health
        assert "evidence_records" in health
        assert "feeds" in health
        assert "agents" in health
        assert "feed_details" in health
        assert "safety_alerts_active" in health
