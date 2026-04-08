"""FDA MedWatch safety alert feed.

Monitors the openFDA adverse event and enforcement endpoints for
safety signals affecting fertility drugs, prenatal supplements, and
related products.

Data source: openFDA (api.fda.gov) — drug/event, drug/enforcement
Cadence: 24 hours
Type: safety
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel

from fertility_sense.feeds.base import BaseFeed
from fertility_sense.models.safety import SafetyAlert, SafetySeverity

logger = logging.getLogger(__name__)

# Fertility-relevant drug names to monitor for adverse events.
_MONITORED_SUBSTANCES: list[str] = [
    "clomiphene",
    "letrozole",
    "gonadotropin",
    "progesterone",
    "estradiol",
    "leuprolide",
    "ganirelix",
    "cetrorelix",
    "cabergoline",
    "metformin",  # Used off-label for PCOS fertility.
    "prenatal vitamin",
    "folic acid",
    "coenzyme q10",
    "DHEA",
]


class FdaAlertsFeed(BaseFeed):
    """Safety feed monitoring openFDA MedWatch for fertility-related alerts.

    Covers:
    - Drug adverse event reports (FAERS) for fertility medications.
    - Drug recalls and enforcement actions.
    - Safety communications related to reproductive health products.
    """

    def __init__(self) -> None:
        super().__init__(
            name="fda_alerts",
            source_url="https://api.fda.gov",
            cadence=timedelta(hours=24),
            feed_type="safety",
        )

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Query openFDA adverse event and enforcement endpoints.

        TODO:
        - Use httpx to query api.fda.gov/drug/event.json for each
          monitored substance with receivedate >= since.
        - Also query api.fda.gov/drug/enforcement.json for recalls.
        - Filter events where patient.patientsex=2 (female) and
          reaction terms include fertility/pregnancy-related MedDRA codes.
        - Handle pagination and rate limits (40 req/min without API key).
        - Aggregate event counts per substance for signal detection.
        """
        logger.warning("FdaAlertsFeed.fetch_raw is not yet implemented")
        return []

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Convert openFDA events to SafetyAlert models.

        TODO:
        - Classify severity based on event seriousness fields
          (seriousnessdeath, seriousnesslifethreatening, etc.).
        - Map reaction terms to canonical topic IDs.
        - Deduplicate by safety report ID (safetyreportid).
        - Set action_required based on severity thresholds.
        - Include case count and disproportionality signal in metadata.
        """
        logger.warning("FdaAlertsFeed.normalize is not yet implemented")
        return []
