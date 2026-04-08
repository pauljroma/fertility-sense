"""Demand signal models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SignalSource(str, Enum):
    GOOGLE_TRENDS = "google_trends"
    SEARCH_CONSOLE = "search_console"
    REDDIT = "reddit"
    FORUM = "forum"
    APP_TELEMETRY = "app_telemetry"


class SignalEvent(BaseModel):
    signal_id: str
    source: SignalSource
    raw_query: str = Field(description="Original search/post text")
    canonical_topic_id: Optional[str] = None
    volume: int = Field(ge=0, description="Absolute volume")
    velocity: float = Field(description="Period-over-period change rate")
    sentiment: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    geo: str = "US"
    observed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class DemandSnapshot(BaseModel):
    topic_id: str
    period: str = Field(description="e.g. '2026-W14', '2026-04'")
    total_volume: int = Field(ge=0)
    velocity_7d: float
    velocity_30d: float
    source_breakdown: dict[SignalSource, int] = Field(default_factory=dict)
    top_queries: list[str] = Field(default_factory=list)
    computed_at: datetime = Field(default_factory=datetime.utcnow)
