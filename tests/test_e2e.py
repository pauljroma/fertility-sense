"""End-to-end tests — full pipeline from signal to governed answer."""

import pytest


@pytest.mark.e2e
def test_full_pipeline_smoke():
    """Basic e2e: load ontology, assemble answer, check governance."""
    from pathlib import Path

    from fertility_sense.assembly.assembler import AnswerAssembler
    from fertility_sense.assembly.retriever import EvidenceRetriever
    from fertility_sense.models.evidence import EvidenceGrade, EvidenceRecord
    from fertility_sense.models.topic import RiskTier
    from fertility_sense.ontology.graph import TopicGraph

    # Load ontology
    graph = TopicGraph(taxonomy_path=Path("data/ontology/taxonomy.yaml"))
    assert len(graph) > 0

    # Pick a GREEN topic
    green_topics = graph.get_by_risk_tier(RiskTier.GREEN)
    if not green_topics:
        pytest.skip("No GREEN topics in taxonomy")

    topic = green_topics[0]

    # Create minimal evidence
    evidence = EvidenceRecord(
        evidence_id="e2e-001",
        source_feed="test",
        title="Test evidence",
        url="https://example.com",
        grade=EvidenceGrade.B,
        grade_rationale="Test",
        topics=[topic.topic_id],
        key_findings=["Test finding for e2e"],
    )

    # Assemble answer
    retriever = EvidenceRetriever(evidence_records=[evidence], safety_alerts=[])
    assembler = AnswerAssembler(retriever)
    answer = assembler.assemble(topic, f"tell me about {topic.display_name}")

    # Verify
    assert answer.topic_id == topic.topic_id
    assert answer.provenance is not None
    assert answer.provenance.evidence_ids == ["e2e-001"]
    assert answer.governance_status in ("published", "pending_review", "escalated")
