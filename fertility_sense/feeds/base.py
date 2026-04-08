"""Abstract base feed class for data ingestion."""

from __future__ import annotations

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behaviour on transient failures."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter: bool = True


class CircuitBreaker:
    """Simple circuit breaker: opens after N consecutive failures, resets after timeout."""

    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 300.0) -> None:
        self._failure_count: int = 0
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._last_failure: float = 0.0
        self._state: str = "closed"  # closed, open, half_open

    @property
    def state(self) -> str:
        """Return the current state, transitioning open -> half_open when timeout elapses."""
        if self._state == "open":
            if time.monotonic() - self._last_failure >= self._reset_timeout:
                self._state = "half_open"
        return self._state

    @property
    def is_open(self) -> bool:
        return self.state == "open"

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._state = "open"
            logger.warning(
                "Circuit breaker opened after %d consecutive failures",
                self._failure_count,
            )

    def should_allow(self) -> bool:
        """Return True if a request should be allowed through."""
        state = self.state
        if state == "closed":
            return True
        if state == "half_open":
            return True  # Allow one probe request
        return False  # open


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
        retry_config: RetryConfig | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.name = name
        self.source_url = source_url
        self.cadence = cadence
        self.feed_type = feed_type
        self.retry_config = retry_config or RetryConfig()
        self.timeout_seconds = timeout_seconds
        self.circuit_breaker = CircuitBreaker()
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

        This is the primary entry-point callers should use.  Includes
        circuit-breaker check, retry with exponential back-off + jitter,
        and per-fetch timeout.
        """
        # Circuit breaker gate
        if not self.circuit_breaker.should_allow():
            logger.warning("%s: circuit breaker open — skipping ingest", self.name)
            return []

        cfg = self.retry_config
        last_exc: Exception | None = None

        for attempt in range(1, cfg.max_attempts + 1):
            try:
                raw = await asyncio.wait_for(
                    self.fetch_raw(since),
                    timeout=self.timeout_seconds,
                )
                records = self.normalize(raw)
                self._last_success = datetime.now(tz=timezone.utc)
                self._records_ingested += len(records)
                self.circuit_breaker.record_success()
                logger.info(
                    "%s: ingested %d records (total %d)",
                    self.name,
                    len(records),
                    self._records_ingested,
                )
                return records
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "%s: attempt %d/%d failed: %s",
                    self.name,
                    attempt,
                    cfg.max_attempts,
                    exc,
                )
                if attempt < cfg.max_attempts:
                    delay = min(cfg.base_delay * (2 ** (attempt - 1)), cfg.max_delay)
                    if cfg.jitter:
                        delay *= random.uniform(0.5, 1.5)
                    await asyncio.sleep(delay)

        # All attempts exhausted
        self.circuit_breaker.record_failure()
        self._last_error = str(last_exc)
        self._last_error_at = datetime.now(tz=timezone.utc)
        logger.exception("%s: ingest failed after %d attempts", self.name, cfg.max_attempts)
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
