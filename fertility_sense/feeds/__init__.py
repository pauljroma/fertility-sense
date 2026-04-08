"""Data feed ingestion layer.

Feed classes are imported lazily to avoid requiring optional dependencies
(pytrends, praw, beautifulsoup4) at import time.
"""

from fertility_sense.feeds.base import BaseFeed, FeedHealth
from fertility_sense.feeds.registry import FeedRegistry

__all__ = [
    "BaseFeed",
    "FeedHealth",
    "FeedRegistry",
]
