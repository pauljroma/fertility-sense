"""Topic classifier — maps free-text queries to TopicNode objects."""

from __future__ import annotations

import re
from typing import Optional

from fertility_sense.models.topic import TopicNode
from fertility_sense.ontology.graph import TopicGraph
from fertility_sense.ontology.resolver import AliasResolver, _normalize


class TopicClassifier:
    """Classify user queries into the topic ontology.

    Resolution strategy (in priority order):
    1. Exact alias resolution via AliasResolver
    2. Substring match on graph aliases
    3. Keyword overlap scoring against topic aliases and display names
    """

    def __init__(
        self,
        graph: TopicGraph,
        resolver: Optional[AliasResolver] = None,
    ) -> None:
        self._graph = graph
        self._resolver = resolver or AliasResolver()

    def classify_query(self, query: str, graph: Optional[TopicGraph] = None) -> Optional[TopicNode]:
        """Classify a free-text query into the best matching TopicNode.

        Args:
            query: Raw user query string.
            graph: Optional override graph (uses instance graph by default).

        Returns:
            The best-matching TopicNode, or None if no reasonable match.
        """
        g = graph or self._graph
        if not query or not query.strip():
            return None

        # Strategy 1: Exact alias resolution
        topic_id = self._resolver.resolve(query)
        if topic_id:
            node = g.get_topic(topic_id)
            if node:
                return node

        # Strategy 2: Graph substring search (returns exact matches first)
        search_results = g.search(query)
        if search_results:
            return search_results[0]

        # Strategy 3: Keyword overlap scoring
        return self._keyword_match(query, g)

    def _keyword_match(self, query: str, graph: TopicGraph) -> Optional[TopicNode]:
        """Score topics by keyword overlap with the query."""
        query_tokens = set(_tokenize(query))
        if not query_tokens:
            return None

        best_node: Optional[TopicNode] = None
        best_score: float = 0.0

        for topic in graph.all_topics():
            score = self._score_topic(query_tokens, topic)
            if score > best_score:
                best_score = score
                best_node = topic

        # Require at least one token overlap
        if best_score >= 1.0:
            return best_node
        return None

    @staticmethod
    def _score_topic(query_tokens: set[str], topic: TopicNode) -> float:
        """Score a topic against query tokens.

        Scoring:
        - Each overlapping token with an alias: +1.0
        - Each overlapping token with display_name: +0.8
        - Bonus for topic_id token overlap: +0.5
        """
        score = 0.0

        # Alias token overlap
        for alias in topic.aliases:
            alias_tokens = set(_tokenize(alias))
            overlap = query_tokens & alias_tokens
            if overlap:
                # Weight by fraction of alias matched
                alias_score = len(overlap) * (len(overlap) / max(len(alias_tokens), 1))
                score = max(score, alias_score)

        # Display name token overlap
        display_tokens = set(_tokenize(topic.display_name))
        display_overlap = query_tokens & display_tokens
        if display_overlap:
            display_score = len(display_overlap) * 0.8 * (len(display_overlap) / max(len(display_tokens), 1))
            score = max(score, display_score)

        # Topic ID bonus
        id_tokens = set(topic.topic_id.split("-"))
        id_overlap = query_tokens & id_tokens
        if id_overlap:
            score += len(id_overlap) * 0.5

        return score


def _tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens."""
    normalized = _normalize(text)
    return [t for t in re.split(r"[^a-z0-9]+", normalized) if t and len(t) > 1]


def classify_query(query: str, graph: TopicGraph) -> Optional[TopicNode]:
    """Convenience function: classify a query against a TopicGraph.

    Creates a TopicClassifier with default AliasResolver and classifies.
    """
    classifier = TopicClassifier(graph)
    return classifier.classify_query(query)
