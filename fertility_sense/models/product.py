"""Product option models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ProductType(str, Enum):
    CONTENT = "content"     # Article, guide, video
    TOOL = "tool"           # Calculator, tracker, quiz
    REFERRAL = "referral"   # Provider, product, service referral
    COMMERCE = "commerce"   # Affiliate, DTC product


class ProductOption(BaseModel):
    option_id: str
    product_type: ProductType
    topic_id: str
    title: str
    description: str
    estimated_impact: float = Field(ge=0.0, le=1.0)
    estimated_effort: str = Field(description="'small', 'medium', 'large'")
    revenue_model: Optional[str] = None
    priority_score: float = Field(ge=0.0, description="Derived from TOS")
    status: str = "proposed"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentBrief(BaseModel):
    brief_id: str
    topic_id: str
    title: str
    angle: str
    target_length_words: int = Field(ge=100)
    evidence_requirements: list[str] = Field(default_factory=list)
    target_audience: str
    journey_stage: str
    seo_keywords: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
