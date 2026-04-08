"""CDC ART/NASS (Assisted Reproductive Technology / National ART Surveillance System) feed.

Ingests clinic-level IVF success-rate data published annually by the CDC,
covering cycle counts, live-birth rates, and patient demographics.

Data source: https://www.cdc.gov/art/
Cadence: 30 days
Type: evidence
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel

from fertility_sense.feeds.base import BaseFeed
from fertility_sense.models.clinic import ClinicRecord
from fertility_sense.models.evidence import EvidenceGrade, EvidenceRecord

logger = logging.getLogger(__name__)


class CdcArtNassFeed(BaseFeed):
    """Evidence feed from CDC ART/NASS clinic success-rate reports.

    The CDC requires all US fertility clinics to report outcomes
    annually.  This feed ingests clinic-level data including:
    - Number of cycles performed by type (fresh, frozen, donor)
    - Live-birth rates by age group
    - Singleton vs. multiple birth rates
    - Patient demographics and diagnoses
    """

    def __init__(self) -> None:
        super().__init__(
            name="cdc_art_nass",
            source_url="https://www.cdc.gov/art/",
            cadence=timedelta(days=30),
            feed_type="evidence",
        )

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Fetch ART success-rate data from the CDC.

        TODO:
        - Download the annual ART data CSV/Excel from the CDC data portal.
        - Check for new report year availability.
        - Parse clinic-level rows with success metrics by age band.
        - Also pull the national summary statistics.
        - Handle the ~2 year reporting lag (2024 data arrives ~2026).
        """
        logger.warning("CdcArtNassFeed.fetch_raw is not yet implemented")
        return []

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Convert ART data to EvidenceRecord and ClinicRecord models.

        TODO:
        - Create ClinicRecord per clinic with success_rates dict.
        - Create EvidenceRecord per national-level finding.
        - Grade as EvidenceGrade.A (national registry, mandatory reporting).
        - Populate topics: ivf, egg_freezing, donor_egg, etc.
        - Map SART IDs and NPI numbers where available.
        """
        logger.warning("CdcArtNassFeed.normalize is not yet implemented")
        return []
