"""Feed registry — discovers, stores, and orchestrates all feeds."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from fertility_sense.feeds.base import BaseFeed, FeedHealth

logger = logging.getLogger(__name__)


class FeedRegistry:
    """Central registry that tracks every registered feed.

    Usage::

        registry = FeedRegistry()
        registry.register(google_trends_feed)
        registry.register(reddit_feed)

        report = registry.health_report()
        results = await registry.run_all(since=some_datetime)
    """

    def __init__(self) -> None:
        self._feeds: dict[str, BaseFeed] = {}

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
    # Execution
    # ------------------------------------------------------------------

    async def run_all(self, since: datetime) -> dict[str, list[BaseModel]]:
        """Run every registered feed concurrently.

        Returns a dict mapping feed name to its normalised records.
        """
        tasks = {
            name: asyncio.create_task(feed.ingest(since))
            for name, feed in self._feeds.items()
        }
        results: dict[str, list[BaseModel]] = {}
        for name, task in tasks.items():
            results[name] = await task
        return results

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
                feed.ingest(now - feed.cadence)
            )
            for name, feed in due_feeds.items()
        }
        results: dict[str, list[BaseModel]] = {}
        for name, task in tasks.items():
            results[name] = await task
        return results

    def __len__(self) -> int:
        return len(self._feeds)

    def __repr__(self) -> str:
        return f"<FeedRegistry feeds={len(self._feeds)}>"
