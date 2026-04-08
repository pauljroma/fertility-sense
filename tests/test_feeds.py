"""Integration tests for feed infrastructure."""

import pytest
from datetime import timedelta

from fertility_sense.feeds.base import BaseFeed, FeedHealth

try:
    from pytrends.request import TrendReq

    _has_pytrends = True
except ImportError:
    _has_pytrends = False


@pytest.mark.unit
def test_feed_health_model():
    health = FeedHealth(
        feed_name="test_feed",
        records_ingested=100,
        is_stale=False,
    )
    assert health.feed_name == "test_feed"
    assert health.records_ingested == 100


@pytest.mark.unit
@pytest.mark.skipif(not _has_pytrends, reason="pytrends not installed")
def test_google_trends_feed_init():
    from fertility_sense.feeds.google_trends import GoogleTrendsFeed

    feed = GoogleTrendsFeed()
    assert feed.name == "google_trends"
    assert feed.feed_type == "demand"
    assert feed.cadence == timedelta(hours=6)


@pytest.mark.unit
def test_google_trends_feed_import_error():
    """GoogleTrendsFeed raises ImportError when pytrends is missing."""
    from fertility_sense.feeds.google_trends import GoogleTrendsFeed, TrendReq

    if TrendReq is None:
        with pytest.raises(ImportError, match="pytrends"):
            GoogleTrendsFeed()


@pytest.mark.unit
def test_reddit_feed_init():
    from fertility_sense.config import FertilitySenseConfig
    from fertility_sense.feeds.reddit import RedditFeed

    cfg = FertilitySenseConfig(reddit_client_id="test-id", reddit_client_secret="test-secret")
    feed = RedditFeed(config=cfg)
    assert feed.name == "reddit"
    assert feed.feed_type == "demand"


@pytest.mark.unit
def test_mother_to_baby_feed_init():
    from fertility_sense.feeds.mother_to_baby import MotherToBabyFeed

    feed = MotherToBabyFeed()
    assert feed.name == "mother_to_baby"
    assert feed.feed_type == "evidence"


@pytest.mark.unit
@pytest.mark.skipif(not _has_pytrends, reason="pytrends not installed")
def test_feed_registry():
    from fertility_sense.feeds.registry import FeedRegistry
    from fertility_sense.feeds.google_trends import GoogleTrendsFeed

    registry = FeedRegistry()
    feed = GoogleTrendsFeed()
    registry.register(feed)

    assert registry.get("google_trends") is feed
    assert len(registry.all_feeds()) == 1
    assert len(registry.by_type("demand")) == 1
    assert len(registry.by_type("evidence")) == 0


@pytest.mark.unit
@pytest.mark.skipif(not _has_pytrends, reason="pytrends not installed")
def test_feed_health_report():
    from fertility_sense.feeds.registry import FeedRegistry
    from fertility_sense.feeds.google_trends import GoogleTrendsFeed

    registry = FeedRegistry()
    registry.register(GoogleTrendsFeed())

    report = registry.health_report()
    assert len(report) == 1
    assert report[0].feed_name == "google_trends"
