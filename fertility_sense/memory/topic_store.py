"""Topic graph persistence store."""

from __future__ import annotations

import json
from pathlib import Path

from fertility_sense.models.topic import TopicNode


class TopicStore:
    """File-backed store for topic nodes."""

    def __init__(self, store_dir: Path) -> None:
        self._dir = store_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._topics: dict[str, TopicNode] = {}

    def put(self, topic: TopicNode) -> None:
        self._topics[topic.topic_id] = topic
        path = self._dir / f"{topic.topic_id}.json"
        path.write_text(topic.model_dump_json(indent=2))

    def get(self, topic_id: str) -> TopicNode | None:
        if topic_id in self._topics:
            return self._topics[topic_id]
        path = self._dir / f"{topic_id}.json"
        if path.exists():
            topic = TopicNode.model_validate_json(path.read_text())
            self._topics[topic_id] = topic
            return topic
        return None

    def all_topics(self) -> list[TopicNode]:
        for path in self._dir.glob("*.json"):
            topic_id = path.stem
            if topic_id not in self._topics:
                self._topics[topic_id] = TopicNode.model_validate_json(path.read_text())
        return list(self._topics.values())

    def count(self) -> int:
        return len(list(self._dir.glob("*.json")))
