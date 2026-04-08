"""Abstract base feed class for data ingestion."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FeedHealth(BaseModel):
    """Health status snapshot for a single feed."""

    feed_name: str
    last_success: datetime | None = None
    last_error: str | None = None
    last_error_at: datetime | None = None
    records_ingested: int = 0
    is_stale: bool = False
    staleness_seconds: float = 0.0


class BaseFeed(ABC):
    """Base class all data feeds must extend.

    Subclasses implement ``fetch_raw`` (IO) and ``normalize`` (parsing).
    The ``ingest`` orchestrator calls both, tracks health, and returns
    normalised Pydantic models ready for downstream scoring.
    """

    name: str
    source_url: str
    cadence: timedelta
    feed_type: str  # "demand", "evidence", "safety"

    def __init__(
        self,
        name: str,
        source_url: str,
        cadence: timedelta,
        feed_type: str,
    ) -> None:
        self.name = name
        self.source_url = source_url
        self.cadence = cadence
        self.feed_type = feed_type
        self._last_success: datetime | None = None
        self._last_error: str | None = None
        self._last_error_at: datetime | None = None
        self._records_ingested: int = 0

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Fetch raw records from the upstream source.

        Parameters
        ----------
        since:
            Only fetch records newer than this timestamp.

        Returns
        -------
        list[dict]
            Raw JSON-like dicts straight from the source.
        """
        ...

    @abstractmethod
    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Transform raw dicts into domain Pydantic models.

        Parameters
        ----------
        raw:
            Output of ``fetch_raw``.

        Returns
        -------
        list[BaseModel]
            Normalised ``SignalEvent``, ``EvidenceRecord``, ``SafetyAlert``, etc.
        """
        ...

    # ------------------------------------------------------------------
    # Orchestrator
    # ------------------------------------------------------------------

    async def ingest(self, since: datetime) -> list[BaseModel]:
        """Fetch, normalise, and track health in one call.

        This is the primary entry-point callers should use.
        """
        try:
            raw = await self.fetch_raw(since)
            records = self.normalize(raw)
            self._last_success = datetime.now(tz=timezone.utc)
            self._records_ingested += len(records)
            logger.info(
                "%s: ingested %d records (total %d)",
                self.name,
                len(records),
                self._records_ingested,
            )
            return records
        except Exception as exc:
            self._last_error = str(exc)
            self._last_error_at = datetime.now(tz=timezone.utc)
            logger.exception("%s: ingest failed", self.name)
            return []

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health(self) -> FeedHealth:
        """Return a point-in-time health snapshot."""
        now = datetime.now(tz=timezone.utc)
        staleness = 0.0
        is_stale = False
        if self._last_success is not None:
            staleness = (now - self._last_success).total_seconds()
            is_stale = staleness > self.cadence.total_seconds() * 2
        else:
            # Never succeeded — considered stale from the start.
            is_stale = True

        return FeedHealth(
            feed_name=self.name,
            last_success=self._last_success,
            last_error=self._last_error,
            last_error_at=self._last_error_at,
            records_ingested=self._records_ingested,
            is_stale=is_stale,
            staleness_seconds=staleness,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def is_due(self, now: datetime) -> bool:
        """Return True if enough time has passed since the last ingest."""
        if self._last_success is None:
            return True
        return (now - self._last_success).total_seconds() >= self.cadence.total_seconds()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r} type={self.feed_type!r}>"
