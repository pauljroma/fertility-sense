"""Tests for feed resilience: retry, circuit breaker, concurrency control."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from fertility_sense.feeds.base import BaseFeed, CircuitBreaker, RetryConfig
from fertility_sense.feeds.registry import FeedRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class DummyRecord(BaseModel):
    value: str = "ok"


class StubFeed(BaseFeed):
    """Concrete feed for testing — fetch_raw and normalize are overridable."""

    def __init__(
        self,
        name: str = "stub",
        fail_n_times: int = 0,
        records: list[dict[str, Any]] | None = None,
        retry_config: RetryConfig | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        super().__init__(
            name=name,
            source_url="https://example.com",
            cadence=timedelta(hours=1),
            feed_type="demand",
            retry_config=retry_config,
            timeout_seconds=timeout_seconds,
        )
        self._fail_n_times = fail_n_times
        self._call_count = 0
        self._records = records or [{"v": "1"}]

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        self._call_count += 1
        if self._call_count <= self._fail_n_times:
            raise RuntimeError(f"Simulated failure #{self._call_count}")
        return self._records

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        return [DummyRecord(value=str(r.get("v", ""))) for r in raw]


class SlowFeed(StubFeed):
    """Feed that takes longer than the timeout."""

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        await asyncio.sleep(10)
        return [{"v": "slow"}]


class TrackingFeed(StubFeed):
    """Feed that records timestamps when it starts/stops running."""

    def __init__(self, name: str, delay: float = 0.1, **kwargs: Any) -> None:
        super().__init__(name=name, **kwargs)
        self._delay = delay
        self.started_at: float | None = None
        self.finished_at: float | None = None

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        self.started_at = time.monotonic()
        await asyncio.sleep(self._delay)
        self.finished_at = time.monotonic()
        return [{"v": "1"}]


# ---------------------------------------------------------------------------
# RetryConfig tests
# ---------------------------------------------------------------------------


class TestRetryConfig:
    def test_defaults(self) -> None:
        cfg = RetryConfig()
        assert cfg.max_attempts == 3
        assert cfg.base_delay == 1.0
        assert cfg.max_delay == 30.0
        assert cfg.jitter is True

    def test_custom_values(self) -> None:
        cfg = RetryConfig(max_attempts=5, base_delay=0.5, max_delay=10.0, jitter=False)
        assert cfg.max_attempts == 5
        assert cfg.base_delay == 0.5


# ---------------------------------------------------------------------------
# CircuitBreaker tests
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    def test_starts_closed(self) -> None:
        cb = CircuitBreaker()
        assert cb.state == "closed"
        assert cb.should_allow() is True
        assert cb.is_open is False

    def test_opens_after_threshold_failures(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.state == "open"
        assert cb.should_allow() is False
        assert cb.is_open is True

    def test_does_not_open_below_threshold(self) -> None:
        cb = CircuitBreaker(failure_threshold=5)
        for _ in range(4):
            cb.record_failure()
        assert cb.state == "closed"
        assert cb.should_allow() is True

    def test_success_resets_failure_count(self) -> None:
        cb = CircuitBreaker(failure_threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        # After success, even two more failures shouldn't open it.
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "closed"

    def test_resets_to_half_open_after_timeout(self) -> None:
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.05)
        cb.record_failure()
        assert cb.state == "open"
        # Wait for the reset timeout.
        time.sleep(0.1)
        assert cb.state == "half_open"
        assert cb.should_allow() is True

    def test_half_open_success_closes(self) -> None:
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.05)
        cb.record_failure()
        time.sleep(0.1)
        assert cb.state == "half_open"
        cb.record_success()
        assert cb.state == "closed"

    def test_half_open_failure_reopens(self) -> None:
        cb = CircuitBreaker(failure_threshold=1, reset_timeout=0.05)
        cb.record_failure()
        time.sleep(0.1)
        assert cb.state == "half_open"
        cb.record_failure()
        assert cb.state == "open"


# ---------------------------------------------------------------------------
# BaseFeed.ingest() tests
# ---------------------------------------------------------------------------


class TestBaseFeedIngest:
    async def test_success_no_retry(self) -> None:
        feed = StubFeed(retry_config=RetryConfig(max_attempts=3, base_delay=0.01))
        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        records = await feed.ingest(since)
        assert len(records) == 1
        assert feed._call_count == 1

    async def test_retries_on_failure_then_succeeds(self) -> None:
        feed = StubFeed(
            fail_n_times=2,
            retry_config=RetryConfig(max_attempts=3, base_delay=0.01, jitter=False),
        )
        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        records = await feed.ingest(since)
        assert len(records) == 1
        assert feed._call_count == 3  # 2 failures + 1 success

    async def test_exhausts_retries_returns_empty(self) -> None:
        feed = StubFeed(
            fail_n_times=5,
            retry_config=RetryConfig(max_attempts=3, base_delay=0.01, jitter=False),
        )
        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        records = await feed.ingest(since)
        assert records == []
        assert feed._call_count == 3
        assert feed._last_error is not None

    async def test_circuit_breaker_blocks_when_open(self) -> None:
        feed = StubFeed()
        # Manually open the circuit breaker.
        feed.circuit_breaker._state = "open"
        feed.circuit_breaker._last_failure = time.monotonic()  # recent
        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        records = await feed.ingest(since)
        assert records == []
        assert feed._call_count == 0  # Never even attempted

    async def test_timeout_triggers_retry(self) -> None:
        feed = SlowFeed(
            retry_config=RetryConfig(max_attempts=2, base_delay=0.01, jitter=False),
            timeout_seconds=0.05,
        )
        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        records = await feed.ingest(since)
        assert records == []  # Both attempts should time out

    async def test_ingest_records_success_to_circuit_breaker(self) -> None:
        feed = StubFeed(retry_config=RetryConfig(max_attempts=1, base_delay=0.01))
        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        await feed.ingest(since)
        assert feed.circuit_breaker.state == "closed"
        assert feed.circuit_breaker._failure_count == 0

    async def test_ingest_records_failure_to_circuit_breaker(self) -> None:
        feed = StubFeed(
            fail_n_times=10,
            retry_config=RetryConfig(max_attempts=1, base_delay=0.01),
        )
        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        await feed.ingest(since)
        assert feed.circuit_breaker._failure_count == 1


# ---------------------------------------------------------------------------
# FeedRegistry tests
# ---------------------------------------------------------------------------


class TestFeedRegistry:
    async def test_run_all_handles_partial_failures(self) -> None:
        """One feed failing should not prevent others from returning results."""
        good_feed = StubFeed(name="good")
        bad_feed = StubFeed(
            name="bad",
            fail_n_times=10,
            retry_config=RetryConfig(max_attempts=1, base_delay=0.01),
        )

        registry = FeedRegistry(max_concurrent=5)
        registry.register(good_feed)
        registry.register(bad_feed)

        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        results = await registry.run_all(since)

        assert len(results["good"]) == 1  # Succeeded
        assert results["bad"] == []  # Failed gracefully

    async def test_run_all_structured_returns_per_feed_status(self) -> None:
        good_feed = StubFeed(name="good")
        bad_feed = StubFeed(
            name="bad",
            fail_n_times=10,
            retry_config=RetryConfig(max_attempts=1, base_delay=0.01),
        )

        registry = FeedRegistry(max_concurrent=5)
        registry.register(good_feed)
        registry.register(bad_feed)

        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        results = await registry.run_all_structured(since)

        by_name = {r.feed_name: r for r in results}
        assert by_name["good"].status == "success"
        assert by_name["good"].record_count == 1
        assert by_name["bad"].status == "success"  # ingest returns [] on failure, not exception
        assert by_name["bad"].record_count == 0

    async def test_max_concurrent_limits_parallelism(self) -> None:
        """With max_concurrent=1, feeds should run sequentially."""
        feed_a = TrackingFeed(name="a", delay=0.1)
        feed_b = TrackingFeed(name="b", delay=0.1)

        registry = FeedRegistry(max_concurrent=1)
        registry.register(feed_a)
        registry.register(feed_b)

        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        await registry.run_all(since)

        # With max_concurrent=1, one feed must finish before the other starts.
        assert feed_a.started_at is not None
        assert feed_a.finished_at is not None
        assert feed_b.started_at is not None
        assert feed_b.finished_at is not None

        # Verify no overlap: one must start after the other finishes.
        if feed_a.started_at < feed_b.started_at:
            assert feed_a.finished_at <= feed_b.started_at + 0.01  # small tolerance
        else:
            assert feed_b.finished_at <= feed_a.started_at + 0.01

    async def test_max_concurrent_allows_parallel(self) -> None:
        """With max_concurrent=2, both feeds should run in parallel."""
        feed_a = TrackingFeed(name="a", delay=0.1)
        feed_b = TrackingFeed(name="b", delay=0.1)

        registry = FeedRegistry(max_concurrent=2)
        registry.register(feed_a)
        registry.register(feed_b)

        since = datetime.now(tz=timezone.utc) - timedelta(hours=1)
        await registry.run_all(since)

        assert feed_a.started_at is not None
        assert feed_b.started_at is not None

        # Both should start close to the same time.
        assert abs(feed_a.started_at - feed_b.started_at) < 0.05

    async def test_run_due_only_runs_due_feeds(self) -> None:
        feed_a = StubFeed(name="due_feed")
        feed_b = StubFeed(name="not_due_feed")

        # Simulate feed_b having succeeded recently.
        feed_b._last_success = datetime.now(tz=timezone.utc)

        registry = FeedRegistry(max_concurrent=5)
        registry.register(feed_a)
        registry.register(feed_b)

        now = datetime.now(tz=timezone.utc)
        results = await registry.run_due(now)

        assert "due_feed" in results
        assert "not_due_feed" not in results
