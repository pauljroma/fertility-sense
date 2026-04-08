"""Feed registry — discovers, stores, and orchestrates all feeds."""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from fertility_sense.feeds.base import BaseFeed, FeedHealth

logger = logging.getLogger(__name__)


@dataclass
class FeedResult:
    """Result from a single feed execution."""

    feed_name: str
    status: str  # "success", "error", "skipped"
    records: list[BaseModel] = field(default_factory=list)
    error: str | None = None
    record_count: int = 0


class FeedRegistry:
    """Central registry that tracks every registered feed.

    Usage::

        registry = FeedRegistry(max_concurrent=3)
        registry.register(google_trends_feed)
        registry.register(reddit_feed)

        report = registry.health_report()
        results = await registry.run_all(since=some_datetime)
    """

    def __init__(self, max_concurrent: int = 3) -> None:
        self._feeds: dict[str, BaseFeed] = {}
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, feed: BaseFeed) -> None:
        """Register a feed. Raises if a duplicate name is detected."""
        if feed.name in self._feeds:
            raise ValueError(f"Feed {feed.name!r} already registered")
        self._feeds[feed.name] = feed
        logger.info("Registered feed: %s (%s)", feed.name, feed.feed_type)

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get(self, name: str) -> BaseFeed:
        """Retrieve a feed by name. Raises KeyError if missing."""
        return self._feeds[name]

    def all_feeds(self) -> list[BaseFeed]:
        """Return every registered feed."""
        return list(self._feeds.values())

    def by_type(self, feed_type: str) -> list[BaseFeed]:
        """Return feeds matching a given type (demand/evidence/safety)."""
        return [f for f in self._feeds.values() if f.feed_type == feed_type]

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_report(self) -> list[FeedHealth]:
        """Aggregate health from every registered feed."""
        return [f.health() for f in self._feeds.values()]

    # ------------------------------------------------------------------
    # Execution helpers
    # ------------------------------------------------------------------

    async def _run_feed(
        self, feed: BaseFeed, since: datetime
    ) -> FeedResult:
        """Run a single feed with semaphore-based concurrency control."""
        async with self._semaphore:
            try:
                records = await feed.ingest(since)
                return FeedResult(
                    feed_name=feed.name,
                    status="success",
                    records=records,
                    record_count=len(records),
                )
            except Exception as exc:
                logger.exception("Feed %s failed unexpectedly", feed.name)
                return FeedResult(
                    feed_name=feed.name,
                    status="error",
                    error=str(exc),
                )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    async def run_all(self, since: datetime) -> dict[str, list[BaseModel]]:
        """Run every registered feed concurrently with bounded parallelism.

        Returns a dict mapping feed name to its normalised records.
        One feed failing does not stop the others.
        """
        tasks = {
            name: asyncio.create_task(self._run_feed(feed, since))
            for name, feed in self._feeds.items()
        }
        results: dict[str, list[BaseModel]] = {}
        for name, task in tasks.items():
            result = await task
            results[name] = result.records
        return results

    async def run_all_structured(self, since: datetime) -> list[FeedResult]:
        """Run every registered feed and return structured per-feed results."""
        tasks = [
            asyncio.create_task(self._run_feed(feed, since))
            for feed in self._feeds.values()
        ]
        return list(await asyncio.gather(*tasks))

    async def run_due(self, now: datetime) -> dict[str, list[BaseModel]]:
        """Run only the feeds whose cadence window has elapsed.

        ``now`` is also used as the ``since`` parameter so each feed only
        fetches data since its cadence window.
        """
        due_feeds = {
            name: feed
            for name, feed in self._feeds.items()
            if feed.is_due(now)
        }
        if not due_feeds:
            logger.info("No feeds are due for ingestion.")
            return {}

        logger.info(
            "Running %d due feed(s): %s",
            len(due_feeds),
            ", ".join(due_feeds.keys()),
        )

        tasks = {
            name: asyncio.create_task(
                self._run_feed(feed, now - feed.cadence)
            )
            for name, feed in due_feeds.items()
        }
        results: dict[str, list[BaseModel]] = {}
        for name, task in tasks.items():
            result = await task
            results[name] = result.records
        return results

    def __len__(self) -> int:
        return len(self._feeds)

    def __repr__(self) -> str:
        return f"<FeedRegistry feeds={len(self._feeds)}>"
