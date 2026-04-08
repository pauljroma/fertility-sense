"""Governance audit trail."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from fertility_sense.models.evidence import EvidenceGrade
from fertility_sense.models.topic import RiskTier


class AuditEntry(BaseModel):
    answer_id: str
    topic_id: str
    risk_tier: RiskTier
    evidence_grade: EvidenceGrade | None
    governance_decision: str
    violations: list[str] = Field(default_factory=list)
    reviewer: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditLog:
    """Append-only governance audit log backed by JSON-L files."""

    def __init__(self, log_dir: Path) -> None:
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self, date: datetime) -> Path:
        return self._log_dir / f"audit_{date.strftime('%Y-%m-%d')}.jsonl"

    def record(self, entry: AuditEntry) -> None:
        """Append an audit entry to the daily log."""
        path = self._log_path(entry.timestamp)
        with open(path, "a") as f:
            f.write(entry.model_dump_json() + "\n")

    def query(
        self,
        date: datetime,
        topic_id: str | None = None,
        decision: str | None = None,
    ) -> list[AuditEntry]:
        """Query audit entries for a given date, optionally filtered."""
        path = self._log_path(date)
        if not path.exists():
            return []
        entries: list[AuditEntry] = []
        for line in path.read_text().strip().split("\n"):
            if not line:
                continue
            entry = AuditEntry.model_validate(json.loads(line))
            if topic_id and entry.topic_id != topic_id:
                continue
            if decision and entry.governance_decision != decision:
                continue
            entries.append(entry)
        return entries
