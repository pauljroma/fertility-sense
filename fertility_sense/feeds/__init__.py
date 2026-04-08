"""Data feed ingestion layer.

Feed classes are imported lazily to avoid requiring optional dependencies
(pytrends, praw, beautifulsoup4) at import time.
"""

from fertility_sense.feeds.base import BaseFeed, CircuitBreaker, FeedHealth, RetryConfig
from fertility_sense.feeds.registry import FeedRegistry

__all__ = [
    "BaseFeed",
    "CircuitBreaker",
    "FeedHealth",
    "FeedRegistry",
    "RetryConfig",
]
