"""Safety alert models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SafetySeverity(str, Enum):
    CRITICAL = "critical"  # Immediate withdrawal required
    HIGH = "high"          # Urgent review, possible escalation
    MEDIUM = "medium"      # Flag for next review cycle
    LOW = "low"            # Informational


class SafetyAlert(BaseModel):
    alert_id: str
    source: str = Field(description="e.g. 'fda_medwatch', 'fda_pllr', 'mother_to_baby'")
    title: str
    severity: SafetySeverity
    affected_substances: list[str] = Field(description="Drug names, supplements, chemicals")
    affected_topics: list[str] = Field(description="Canonical topic IDs")
    risk_category: Optional[str] = None
    description: str
    action_required: str = Field(
        description="'withdraw_content', 'add_warning', 'monitor', 'none'"
    )
    url: str
    published_at: datetime
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
