"""Clinic record models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ClinicRecord(BaseModel):
    clinic_id: str
    name: str
    npi: Optional[str] = None
    sart_id: Optional[str] = Field(default=None, description="SART member ID")
    specialties: list[str] = Field(default_factory=list)
    location: dict[str, Any] = Field(
        default_factory=dict,
        description="city, state, zip, lat, lng",
    )
    success_rates: Optional[dict[str, Any]] = Field(
        default=None, description="From CDC ART/NASS"
    )
    accepts_insurance: list[str] = Field(default_factory=list)
    url: Optional[str] = None
    last_verified: datetime = Field(default_factory=datetime.utcnow)
