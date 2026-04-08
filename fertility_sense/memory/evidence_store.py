"""Evidence record store."""

from __future__ import annotations

import json
from pathlib import Path

from fertility_sense.models.evidence import EvidenceRecord


class EvidenceStore:
    """File-backed evidence record store."""

    def __init__(self, store_dir: Path) -> None:
        self._dir = store_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, EvidenceRecord] = {}

    def put(self, record: EvidenceRecord) -> None:
        self._records[record.evidence_id] = record
        path = self._dir / f"{record.evidence_id}.json"
        path.write_text(record.model_dump_json(indent=2))

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        if evidence_id in self._records:
            return self._records[evidence_id]
        path = self._dir / f"{evidence_id}.json"
        if path.exists():
            record = EvidenceRecord.model_validate_json(path.read_text())
            self._records[evidence_id] = record
            return record
        return None

    def by_topic(self, topic_id: str) -> list[EvidenceRecord]:
        self._load_all()
        return [r for r in self._records.values() if topic_id in r.topics]

    def all_records(self) -> list[EvidenceRecord]:
        self._load_all()
        return list(self._records.values())

    def _load_all(self) -> None:
        for path in self._dir.glob("*.json"):
            eid = path.stem
            if eid not in self._records:
                self._records[eid] = EvidenceRecord.model_validate_json(path.read_text())
