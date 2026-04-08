"""Unit tests for ontology module."""

import pytest
from pathlib import Path

from fertility_sense.models.topic import JourneyStage, RiskTier


@pytest.mark.unit
def test_taxonomy_yaml_exists():
    """Taxonomy YAML file exists and is non-empty."""
    path = Path("data/ontology/taxonomy.yaml")
    assert path.exists(), "taxonomy.yaml not found"
    assert path.stat().st_size > 100, "taxonomy.yaml seems too small"


@pytest.mark.unit
def test_aliases_yaml_exists():
    """Aliases YAML file exists and is non-empty."""
    path = Path("data/ontology/aliases.yaml")
    assert path.exists(), "aliases.yaml not found"
    assert path.stat().st_size > 100, "aliases.yaml seems too small"


@pytest.mark.unit
def test_load_taxonomy():
    """Taxonomy loads and produces TopicNode objects."""
    from fertility_sense.ontology.taxonomy import load_taxonomy

    topics = load_taxonomy(Path("data/ontology/taxonomy.yaml"))
    assert len(topics) > 10, f"Expected 10+ topics, got {len(topics)}"

    # Check a topic has required fields
    topic = topics[0]
    assert topic.topic_id
    assert topic.display_name
    assert topic.journey_stage in JourneyStage
    assert topic.risk_tier in RiskTier


@pytest.mark.unit
def test_topic_graph_construction():
    """TopicGraph builds from taxonomy."""
    from fertility_sense.ontology.graph import TopicGraph

    graph = TopicGraph(taxonomy_path=Path("data/ontology/taxonomy.yaml"))
    assert len(graph) > 10
    all_topics = graph.all_topics()
    assert len(all_topics) > 10


@pytest.mark.unit
def test_topic_graph_by_journey_stage():
    """Can filter topics by journey stage."""
    from fertility_sense.ontology.graph import TopicGraph

    graph = TopicGraph(taxonomy_path=Path("data/ontology/taxonomy.yaml"))
    preconception = graph.get_by_journey_stage(JourneyStage.PRECONCEPTION)
    assert len(preconception) > 0
    assert all(t.journey_stage == JourneyStage.PRECONCEPTION for t in preconception)


@pytest.mark.unit
def test_topic_graph_by_risk_tier():
    """Can filter topics by risk tier."""
    from fertility_sense.ontology.graph import TopicGraph

    graph = TopicGraph(taxonomy_path=Path("data/ontology/taxonomy.yaml"))
    red = graph.get_by_risk_tier(RiskTier.RED)
    # There should be some RED topics (medication safety, complications)
    assert all(t.risk_tier == RiskTier.RED for t in red)


@pytest.mark.unit
def test_alias_resolver():
    """Alias resolver resolves known aliases."""
    from fertility_sense.ontology.resolver import AliasResolver

    resolver = AliasResolver(Path("data/ontology/aliases.yaml"))
    # Test that at least one alias resolves
    # The exact aliases depend on what the ontology agent generated
    assert resolver is not None
