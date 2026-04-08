"""User interaction models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserInteraction(BaseModel):
    interaction_id: str
    user_id: Optional[str] = None
    session_id: str
    query: str
    resolved_topic_id: Optional[str] = None
    answer_id: Optional[str] = None
    action_taken: Optional[str] = Field(
        default=None,
        description="'read', 'clicked_tool', 'clicked_referral', 'shared'",
    )
    satisfaction: Optional[int] = Field(default=None, ge=1, le=5)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
