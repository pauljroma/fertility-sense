"""Load and parse taxonomy.yaml into TopicNode objects."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from fertility_sense.models.topic import (
    JourneyStage,
    MonetizationClass,
    RiskTier,
    TopicIntent,
    TopicNode,
)

_DEFAULT_TAXONOMY_PATH = Path(__file__).resolve().parents[2] / "data" / "ontology" / "taxonomy.yaml"


def _parse_leaf(
    topic_id: str,
    data: dict,
    parent_id: Optional[str] = None,
) -> TopicNode:
    """Parse a single leaf node dict into a TopicNode."""
    return TopicNode(
        topic_id=topic_id,
        display_name=data["display_name"],
        aliases=data.get("aliases", []),
        journey_stage=JourneyStage(data["journey_stage"]),
        intent=TopicIntent(data["intent"]),
        risk_tier=RiskTier(data["risk_tier"]),
        monetization_class=MonetizationClass(data.get("monetization_class", "content")),
        parent_id=parent_id,
        children=[],
        tags=[],
    )


def _is_leaf(data: dict) -> bool:
    """Check if a dict represents a leaf topic node (has display_name key)."""
    return isinstance(data, dict) and "display_name" in data


def _walk_tree(
    tree: dict,
    parent_id: Optional[str] = None,
) -> list[TopicNode]:
    """Recursively walk the taxonomy tree and collect all leaf TopicNodes."""
    nodes: list[TopicNode] = []
    for key, value in tree.items():
        if not isinstance(value, dict):
            continue
        if _is_leaf(value):
            nodes.append(_parse_leaf(key, value, parent_id=parent_id))
        else:
            # Intermediate category — recurse
            nodes.extend(_walk_tree(value, parent_id=key))
    return nodes


def load_taxonomy(path: Optional[Path] = None) -> list[TopicNode]:
    """Load taxonomy.yaml and return a flat list of TopicNode objects.

    Args:
        path: Path to taxonomy.yaml. Defaults to data/ontology/taxonomy.yaml
              relative to the project root.

    Returns:
        List of all leaf TopicNode instances found in the taxonomy.
    """
    path = path or _DEFAULT_TAXONOMY_PATH
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise ValueError(f"Expected top-level dict in {path}, got {type(raw).__name__}")

    return _walk_tree(raw)
