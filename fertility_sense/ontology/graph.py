"""TopicGraph — DAG built from the taxonomy for fast lookups."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fertility_sense.models.topic import (
    JourneyStage,
    MonetizationClass,
    RiskTier,
    TopicIntent,
    TopicNode,
)
from fertility_sense.ontology.taxonomy import load_taxonomy


class TopicGraph:
    """Directed acyclic graph of topic nodes built from taxonomy.yaml.

    Provides O(1) topic lookup by ID and efficient filtering by
    journey stage, risk tier, and free-text alias search.
    """

    def __init__(self, taxonomy_path: Optional[Path] = None) -> None:
        self._nodes: dict[str, TopicNode] = {}
        self._children_map: dict[str, list[str]] = {}

        topics = load_taxonomy(taxonomy_path)

        for topic in topics:
            self._nodes[topic.topic_id] = topic

        # Build parent -> children mapping and backfill children lists
        for topic in topics:
            if topic.parent_id:
                self._children_map.setdefault(topic.parent_id, []).append(topic.topic_id)

        # Populate children field on each node that has children in the map
        for parent_id, child_ids in self._children_map.items():
            if parent_id in self._nodes:
                self._nodes[parent_id].children = child_ids

    # ---- Core accessors ----

    def get_topic(self, topic_id: str) -> Optional[TopicNode]:
        """Return a single TopicNode by its canonical ID, or None."""
        return self._nodes.get(topic_id)

    def get_children(self, topic_id: str) -> list[TopicNode]:
        """Return direct child TopicNodes of the given topic/category."""
        child_ids = self._children_map.get(topic_id, [])
        return [self._nodes[cid] for cid in child_ids if cid in self._nodes]

    def get_ancestors(self, topic_id: str) -> list[str]:
        """Walk parent_id chain and return ancestor IDs from nearest to root."""
        ancestors: list[str] = []
        current = self._nodes.get(topic_id)
        visited: set[str] = set()
        while current and current.parent_id and current.parent_id not in visited:
            ancestors.append(current.parent_id)
            visited.add(current.parent_id)
            current = self._nodes.get(current.parent_id)
        return ancestors

    # ---- Filtered views ----

    def get_by_journey_stage(self, stage: JourneyStage) -> list[TopicNode]:
        """Return all topics matching the given journey stage."""
        return [t for t in self._nodes.values() if t.journey_stage == stage]

    def get_by_risk_tier(self, tier: RiskTier) -> list[TopicNode]:
        """Return all topics matching the given risk tier."""
        return [t for t in self._nodes.values() if t.risk_tier == tier]

    # ---- Search ----

    def search(self, query: str) -> list[TopicNode]:
        """Simple text match against topic aliases and display names.

        Returns topics where the lowercased query appears as a substring
        of any alias or the display name.  Results are ordered with exact
        alias matches first, then partial matches.
        """
        q = query.lower().strip()
        if not q:
            return []

        exact: list[TopicNode] = []
        partial: list[TopicNode] = []

        for topic in self._nodes.values():
            matched = False
            # Check aliases for exact match
            for alias in topic.aliases:
                if alias.lower() == q:
                    exact.append(topic)
                    matched = True
                    break
            if matched:
                continue
            # Check partial match in aliases or display_name
            for alias in topic.aliases:
                if q in alias.lower():
                    partial.append(topic)
                    matched = True
                    break
            if not matched and q in topic.display_name.lower():
                partial.append(topic)

        return exact + partial

    # ---- Enumerations ----

    def all_topics(self) -> list[TopicNode]:
        """Return all leaf topic nodes in the graph."""
        return list(self._nodes.values())

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, topic_id: str) -> bool:
        return topic_id in self._nodes

    def __repr__(self) -> str:
        return f"TopicGraph(topics={len(self._nodes)})"
