"""Application configuration."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FertilitySenseConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FERTILITY_SENSE_", env_file=".env")

    # Paths
    base_dir: Path = Field(default_factory=lambda: Path.cwd())
    data_dir: Path = Field(default_factory=lambda: Path.cwd() / "data")
    memory_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "memory")
    evidence_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "evidence")
    feed_state_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "feeds")
    taxonomy_path: Path = Field(
        default_factory=lambda: Path.cwd() / "data" / "ontology" / "taxonomy.yaml"
    )
    aliases_path: Path = Field(
        default_factory=lambda: Path.cwd() / "data" / "ontology" / "aliases.yaml"
    )
    cards_dir: Path = Field(default_factory=lambda: Path.cwd() / "cards")

    # Server
    host: str = "127.0.0.1"
    port: int = Field(default=9300, gt=0, le=65535)

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

    # Secrets / API keys
    api_key: str = Field(default="", description="API key for authenticating requests")
    anthropic_api_key: str = Field(default="", description="Anthropic API key")

    # Reddit feed credentials
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "fertility-sense/0.1.0"

    # Model override — use when API key only accesses older models
    # e.g. "claude-3-haiku-20240307" routes all tiers through one model
    model_override: str = Field(default="", description="Force all agents to use this model ID")

    # Email (IONOS SMTP/IMAP)
    email_address: str = ""
    email_password: str = ""
    smtp_host: str = "smtp.ionos.com"
    smtp_port: int = 587
    imap_host: str = "imap.ionos.com"
    imap_port: int = 993
    email_from_name: str = "Fertility Sense"

    # Alert recipient
    alert_email: str = "paul@romatech.com"

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
