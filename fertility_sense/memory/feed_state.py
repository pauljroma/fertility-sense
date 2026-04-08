"""Feed watermark/cursor state tracking."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class FeedWatermark(BaseModel):
    feed_name: str
    last_success: datetime | None = None
    last_cursor: str | None = None
    records_total: int = 0
    last_error: str | None = None


class FeedStateStore:
    """Tracks feed ingestion watermarks."""

    def __init__(self, store_dir: Path) -> None:
        self._dir = store_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._state: dict[str, FeedWatermark] = {}

    def get(self, feed_name: str) -> FeedWatermark:
        if feed_name in self._state:
            return self._state[feed_name]
        path = self._dir / f"{feed_name}.json"
        if path.exists():
            wm = FeedWatermark.model_validate(json.loads(path.read_text()))
            self._state[feed_name] = wm
            return wm
        return FeedWatermark(feed_name=feed_name)

    def update(self, watermark: FeedWatermark) -> None:
        self._state[watermark.feed_name] = watermark
        path = self._dir / f"{watermark.feed_name}.json"
        path.write_text(watermark.model_dump_json(indent=2))

    def all_states(self) -> list[FeedWatermark]:
        for path in self._dir.glob("*.json"):
            name = path.stem
            if name not in self._state:
                self._state[name] = FeedWatermark.model_validate(json.loads(path.read_text()))
        return list(self._state.values())
