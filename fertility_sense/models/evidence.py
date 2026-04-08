"""Evidence record models."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EvidenceGrade(str, Enum):
    A = "A"  # Systematic review / RCT
    B = "B"  # Well-designed cohort / case-control
    C = "C"  # Expert opinion / case series
    D = "D"  # Anecdotal / conflicting
    X = "X"  # Contraindicated (known harm)


# Numeric weights for scoring
EVIDENCE_GRADE_WEIGHTS: dict[EvidenceGrade, float] = {
    EvidenceGrade.A: 1.0,
    EvidenceGrade.B: 0.75,
    EvidenceGrade.C: 0.4,
    EvidenceGrade.D: 0.15,
    EvidenceGrade.X: 1.0,  # High weight because it's definitive (harm)
}


class EvidenceRecord(BaseModel):
    evidence_id: str
    source_feed: str = Field(description="e.g. 'cdc_prams', 'nih_nichd'")
    title: str
    abstract: Optional[str] = None
    url: str
    doi: Optional[str] = None
    publication_date: Optional[date] = None
    grade: EvidenceGrade
    grade_rationale: str = Field(description="Why this grade was assigned")
    topics: list[str] = Field(description="Canonical topic IDs this covers")
    key_findings: list[str] = Field(default_factory=list)
    population: Optional[str] = None
    sample_size: Optional[int] = Field(default=None, ge=0)
    limitations: list[str] = Field(default_factory=list)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
