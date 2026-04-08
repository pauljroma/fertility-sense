"""Topic Opportunity Score models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TopicOpportunityScore(BaseModel):
    topic_id: str
    period: str = Field(description="Scoring period, e.g. '2026-W14'")
    demand_score: float = Field(ge=0.0, le=100.0)
    clinical_importance: float = Field(ge=0.0, le=100.0)
    trust_risk_score: float = Field(ge=0.0, le=100.0, description="Higher = safer to serve")
    commercial_fit: float = Field(ge=0.0, le=100.0)
    composite_tos: float = Field(ge=0.0, le=100.0)
    rank: Optional[int] = None
    unsafe_to_serve: bool = False
    escalate_to_human: bool = False
    computed_at: datetime = Field(default_factory=datetime.utcnow)
    inputs: dict[str, Any] = Field(default_factory=dict, description="Raw inputs for audit")
