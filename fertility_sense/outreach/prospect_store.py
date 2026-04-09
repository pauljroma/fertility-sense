"""Prospect store — JSON-backed persistence for outreach contacts.

Each prospect is stored as an individual JSON file keyed by email hash,
making it safe for concurrent reads and simple to inspect manually.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Prospect(BaseModel):
    """A single outreach prospect."""

    email: str
    name: str = ""
    journey_stage: str = ""  # pre_ttc, trying, treatment
    diagnosis: str = ""  # pcos, male_factor, unexplained, etc.
    source: str = ""  # reddit, email, quiz, import
    tags: list[str] = Field(default_factory=list)
    sequence: str = ""  # Current sequence name
    sequence_step: int = 0
    last_contact: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    engagement_score: float = 0.0


def _email_key(email: str) -> str:
    """Deterministic filename from email address."""
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()[:16]


class ProspectStore:
    """File-backed prospect database.

    Layout::

        store_dir/
          <hash>.json   — one file per prospect
    """

    def __init__(self, store_dir: Path) -> None:
        self._dir = store_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, prospect: Prospect) -> None:
        """Add or overwrite a prospect."""
        path = self._path_for(prospect.email)
        path.write_text(prospect.model_dump_json(indent=2))
        logger.info("Prospect stored: %s", prospect.email)

    def get(self, email: str) -> Prospect | None:
        """Return a prospect by email, or *None*."""
        path = self._path_for(email)
        if not path.exists():
            return None
        return Prospect.model_validate_json(path.read_text())

    def list_all(self) -> list[Prospect]:
        """Return every prospect in the store."""
        prospects: list[Prospect] = []
        for p in sorted(self._dir.glob("*.json")):
            try:
                prospects.append(Prospect.model_validate_json(p.read_text()))
            except Exception:
                logger.warning("Skipping corrupt prospect file: %s", p)
        return prospects

    def by_segment(self, stage: str) -> list[Prospect]:
        """Filter prospects by journey stage."""
        return [p for p in self.list_all() if p.journey_stage == stage]

    def by_sequence(self, sequence: str) -> list[Prospect]:
        """Filter prospects by active sequence name."""
        return [p for p in self.list_all() if p.sequence == sequence]

    def update(self, email: str, **kwargs: object) -> Prospect | None:
        """Update fields on an existing prospect. Returns updated prospect or None."""
        prospect = self.get(email)
        if prospect is None:
            return None
        data = prospect.model_dump()
        data.update(kwargs)
        updated = Prospect.model_validate(data)
        self.add(updated)
        return updated

    def import_csv(self, csv_path: Path) -> int:
        """Import prospects from a CSV file.

        Expected columns: email, name, journey_stage, diagnosis, source, tags
        The *tags* column is comma-separated within the field.

        Returns the number of prospects imported.
        """
        count = 0
        with open(csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                tags_raw = row.get("tags", "")
                tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []
                prospect = Prospect(
                    email=row["email"].strip(),
                    name=row.get("name", "").strip(),
                    journey_stage=row.get("journey_stage", "").strip(),
                    diagnosis=row.get("diagnosis", "").strip(),
                    source=row.get("source", "import").strip() or "import",
                    tags=tags,
                    created_at=datetime.utcnow(),
                )
                self.add(prospect)
                count += 1
        logger.info("Imported %d prospects from %s", count, csv_path)
        return count

    def count(self) -> int:
        """Total number of stored prospects."""
        return len(list(self._dir.glob("*.json")))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _path_for(self, email: str) -> Path:
        return self._dir / f"{_email_key(email)}.json"
