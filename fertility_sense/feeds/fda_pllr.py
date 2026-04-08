"""FDA PLLR (Pregnancy and Lactation Labeling Rule) evidence + safety feed.

Monitors FDA drug labeling updates under the PLLR framework (replaced
the old A/B/C/D/X categories in 2015) for pregnancy, lactation, and
reproductive-potential subsections.

Data source: DailyMed / openFDA drug labeling API
Cadence: 7 days
Type: evidence + safety
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel

from fertility_sense.feeds.base import BaseFeed
from fertility_sense.models.evidence import EvidenceGrade, EvidenceRecord
from fertility_sense.models.safety import SafetyAlert, SafetySeverity

logger = logging.getLogger(__name__)


class FdaPllrFeed(BaseFeed):
    """Evidence + Safety feed from FDA pregnancy/lactation drug labeling.

    The PLLR requires drug labels to include narrative summaries of
    risk data for:
    - Section 8.1: Pregnancy (including labor and delivery)
    - Section 8.2: Lactation
    - Section 8.3: Females and Males of Reproductive Potential

    This feed detects label updates and surfaces new risk information.
    """

    def __init__(self) -> None:
        super().__init__(
            name="fda_pllr",
            source_url="https://api.fda.gov/drug/label.json",
            cadence=timedelta(days=7),
            feed_type="evidence",  # Also produces safety alerts.
        )

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Query the openFDA drug label API for PLLR-relevant updates.

        TODO:
        - Use httpx to query api.fda.gov/drug/label.json.
        - Filter by effective_time >= since (YYYYMMDD format).
        - Search for labels containing pregnancy/lactation sections.
        - Extract sections 8.1, 8.2, 8.3 from the structured labeling.
        - Handle pagination (limit=100, skip offsets).
        - Also check DailyMed for newly posted SPL documents.
        """
        logger.warning("FdaPllrFeed.fetch_raw is not yet implemented")
        return []

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Convert FDA label data to EvidenceRecord and SafetyAlert models.

        TODO:
        - Create EvidenceRecord per label with pregnancy/lactation data.
        - Grade based on data quality described in the label narrative.
        - Create SafetyAlert when label includes contraindications or
          boxed warnings related to pregnancy/fertility.
        - Extract affected substances from openfda.brand_name and
          openfda.generic_name fields.
        - Map to topics via substance-to-topic ontology lookup.
        """
        logger.warning("FdaPllrFeed.normalize is not yet implemented")
        return []
