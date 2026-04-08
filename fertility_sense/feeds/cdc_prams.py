"""CDC PRAMS (Pregnancy Risk Assessment Monitoring System) evidence feed.

Ingests state-level maternal health surveillance data from the CDC PRAMS
system, which surveys mothers about behaviours and experiences before,
during, and after pregnancy.

Data source: https://www.cdc.gov/prams/
Cadence: 30 days (data is released annually but checked monthly)
Type: evidence
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel

from fertility_sense.feeds.base import BaseFeed
from fertility_sense.models.evidence import EvidenceGrade, EvidenceRecord

logger = logging.getLogger(__name__)


class CdcPramsFeed(BaseFeed):
    """Evidence feed from the CDC PRAMS surveillance system.

    PRAMS data covers topics such as:
    - Pre-conception health and contraceptive use
    - Prenatal care and supplement use
    - Substance exposure during pregnancy
    - Breastfeeding initiation and duration
    - Postpartum depression screening
    """

    def __init__(self) -> None:
        super().__init__(
            name="cdc_prams",
            source_url="https://www.cdc.gov/prams/",
            cadence=timedelta(days=30),
            feed_type="evidence",
        )

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Fetch PRAMS data via the CDC data API or data catalogue.

        TODO:
        - Query the CDC WONDER API or PRAMS data portal.
        - Pull indicator-level data for fertility-relevant topics.
        - Filter by reporting year and state.
        - Also check for newly published PRAMS annual reports (PDF).
        - Parse data tables from the PRAMS PRAMStat query tool.
        """
        logger.warning("CdcPramsFeed.fetch_raw is not yet implemented")
        return []

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Convert PRAMS data tables to EvidenceRecord models.

        TODO:
        - Map each indicator to an EvidenceRecord.
        - Grade as EvidenceGrade.B (well-designed population surveillance).
        - Populate topics from the indicator description.
        - Include state-level granularity in metadata.
        - Set population="postpartum women, state-level sample".
        """
        logger.warning("CdcPramsFeed.normalize is not yet implemented")
        return []
