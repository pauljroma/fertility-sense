"""Alias resolver — maps surface forms to canonical topic IDs."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Optional

import yaml

from fertility_sense.models.topic import Alias

_DEFAULT_ALIASES_PATH = Path(__file__).resolve().parents[2] / "data" / "ontology" / "aliases.yaml"


def _normalize(text: str) -> str:
    """Normalize a surface form for matching.

    - NFKC unicode normalization
    - Lowercase
    - Strip leading/trailing whitespace
    - Collapse internal whitespace to single spaces
    - Remove possessives ('s)
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.lower().strip()
    text = re.sub(r"['']\s*s\b", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


class AliasResolver:
    """Resolve user-facing surface forms to canonical topic IDs.

    Loads aliases.yaml and builds a lookup dict keyed on normalized
    surface forms.  Resolution is case-insensitive with basic text
    normalization.
    """

    def __init__(self, aliases_path: Optional[Path] = None) -> None:
        self._aliases: dict[str, Alias] = {}
        self._load(aliases_path or _DEFAULT_ALIASES_PATH)

    def _load(self, path: Path) -> None:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not raw or "aliases" not in raw:
            return

        for entry in raw["aliases"]:
            alias = Alias(
                surface_form=entry["surface_form"],
                canonical_topic_id=entry["canonical_topic_id"],
                source=entry.get("source", "seed"),
                confidence=float(entry.get("confidence", 1.0)),
            )
            key = _normalize(alias.surface_form)
            # Keep highest-confidence alias when duplicates exist
            existing = self._aliases.get(key)
            if existing is None or alias.confidence > existing.confidence:
                self._aliases[key] = alias

    def resolve(self, surface_form: str) -> Optional[str]:
        """Resolve a surface form to its canonical topic_id.

        Returns the canonical topic_id string, or None if no match is found.
        """
        key = _normalize(surface_form)
        alias = self._aliases.get(key)
        return alias.canonical_topic_id if alias else None

    def resolve_with_confidence(self, surface_form: str) -> tuple[Optional[str], float]:
        """Resolve a surface form and return (topic_id, confidence).

        Returns (None, 0.0) if no match is found.
        """
        key = _normalize(surface_form)
        alias = self._aliases.get(key)
        if alias:
            return alias.canonical_topic_id, alias.confidence
        return None, 0.0

    def all_surface_forms(self) -> list[str]:
        """Return all known surface forms (normalized keys)."""
        return list(self._aliases.keys())

    def __len__(self) -> int:
        return len(self._aliases)

    def __repr__(self) -> str:
        return f"AliasResolver(entries={len(self._aliases)})"
