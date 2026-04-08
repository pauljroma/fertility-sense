"""Application configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FertilitySenseConfig:
    # Paths
    base_dir: Path = field(default_factory=lambda: Path.cwd())
    data_dir: Path = field(default_factory=lambda: Path.cwd() / "data")
    memory_dir: Path = field(default_factory=lambda: Path.cwd() / "data" / "memory")
    evidence_dir: Path = field(default_factory=lambda: Path.cwd() / "data" / "evidence")
    feed_state_dir: Path = field(default_factory=lambda: Path.cwd() / "data" / "feeds")
    taxonomy_path: Path = field(
        default_factory=lambda: Path.cwd() / "data" / "ontology" / "taxonomy.yaml"
    )
    aliases_path: Path = field(
        default_factory=lambda: Path.cwd() / "data" / "ontology" / "aliases.yaml"
    )
    cards_dir: Path = field(default_factory=lambda: Path.cwd() / "cards")

    # Server
    host: str = "127.0.0.1"
    port: int = 9300

    # Cost controls
    cost_budget_usd: float = 10.0
    rate_limit_rpm: int = 60

    # Scoring weights
    w_demand: float = 0.30
    w_clinical: float = 0.25
    w_trust: float = 0.25
    w_commercial: float = 0.20

    # Safety gates
    trust_block_threshold: float = 20.0
    clinical_escalation_threshold: float = 80.0
    trust_escalation_threshold: float = 40.0
