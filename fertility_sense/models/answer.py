"""Governed answer models."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .evidence import EvidenceGrade
from .topic import RiskTier, TopicIntent


class Provenance(BaseModel):
    evidence_ids: list[str] = Field(description="Evidence records supporting this answer")
    grade: EvidenceGrade = Field(description="Floor grade across evidence set")
    sources: list[str] = Field(description="Human-readable source labels")
    last_reviewed: datetime
    reviewer: str = Field(description="'evidence-curator' or human reviewer ID")


class AnswerTemplate(BaseModel):
    template_id: str
    name: str
    risk_tier: RiskTier
    intent: TopicIntent
    structure: list[str] = Field(
        description="Section order, e.g. ['summary','evidence','what_to_do','sources']"
    )
    required_evidence_grade: EvidenceGrade
    requires_human_review: bool = False
    escalation_text: Optional[str] = None


class GovernedAnswer(BaseModel):
    answer_id: str
    topic_id: str
    query: str = Field(description="Original user query")
    template_used: str
    risk_tier: RiskTier
    sections: dict[str, str] = Field(description="section_name -> rendered_text")
    provenance: Provenance
    governance_status: str = Field(
        description="'published', 'pending_review', 'escalated', 'withdrawn'"
    )
    escalation_reason: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
