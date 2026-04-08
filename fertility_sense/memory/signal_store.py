"""Signal event log store."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fertility_sense.models.signal import SignalEvent


class SignalStore:
    """Append-only signal event store backed by JSON-L files."""

    def __init__(self, store_dir: Path) -> None:
        self._dir = store_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, date: datetime) -> Path:
        return self._dir / f"signals_{date.strftime('%Y-%m-%d')}.jsonl"

    def append(self, event: SignalEvent) -> None:
        path = self._log_path(event.observed_at)
        with open(path, "a") as f:
            f.write(event.model_dump_json() + "\n")

    def append_batch(self, events: list[SignalEvent]) -> None:
        for event in events:
            self.append(event)

    def query(
        self,
        date: datetime,
        topic_id: str | None = None,
    ) -> list[SignalEvent]:
        path = self._log_path(date)
        if not path.exists():
            return []
        events: list[SignalEvent] = []
        for line in path.read_text().strip().split("\n"):
            if not line:
                continue
            event = SignalEvent.model_validate(json.loads(line))
            if topic_id and event.canonical_topic_id != topic_id:
                continue
            events.append(event)
        return events
