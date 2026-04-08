"""Reddit demand feed.

Monitors fertility-related subreddits via PRAW and converts posts into
``SignalEvent`` records for downstream demand scoring.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel

try:
    import praw
except ImportError:
    praw = None  # type: ignore[assignment]

from fertility_sense.config import FertilitySenseConfig
from fertility_sense.feeds.base import BaseFeed
from fertility_sense.models.signal import SignalEvent, SignalSource

logger = logging.getLogger(__name__)

# Reddit allows 60 requests/min. We add a small delay between subreddit
# fetches to stay comfortably under the limit.
_RATE_LIMIT_DELAY_SECONDS = 1.2

DEFAULT_SUBREDDITS: list[str] = [
    "TryingForABaby",
    "BabyBumps",
    "InfertilityBabies",
    "Pregnant",
    "beyondthebump",
    "infertility",
]

# Lightweight keyword filter — posts mentioning at least one of these
# are kept; the rest are discarded to reduce noise.
RELEVANCE_KEYWORDS: set[str] = {
    "fertility", "ovulation", "ivf", "iui", "tww", "ttc",
    "prenatal", "pregnancy", "pregnant", "miscarriage",
    "implantation", "embryo", "egg freezing", "sperm",
    "pcos", "endo", "endometriosis", "clomid", "letrozole",
    "progesterone", "hcg", "beta", "bfp", "bfn",
    "amh", "follicle", "trigger shot", "retrieval",
}


def _signal_id(post_id: str) -> str:
    return hashlib.sha256(f"reddit:{post_id}".encode()).hexdigest()[:16]


def _is_relevant(text: str) -> bool:
    """Quick keyword filter against lower-cased text."""
    lower = text.lower()
    return any(kw in lower for kw in RELEVANCE_KEYWORDS)


def _estimate_sentiment(text: str) -> float | None:
    """Heuristic sentiment in [-1, 1] based on simple keyword presence.

    This is a placeholder; swap with a proper model later.
    """
    lower = text.lower()
    positive = {"excited", "hopeful", "grateful", "bfp", "success", "happy", "finally"}
    negative = {"devastated", "frustrated", "failed", "loss", "bfn", "anxious", "scared"}
    pos = sum(1 for w in positive if w in lower)
    neg = sum(1 for w in negative if w in lower)
    total = pos + neg
    if total == 0:
        return None
    return round((pos - neg) / total, 2)


class RedditFeed(BaseFeed):
    """Demand feed monitoring fertility-related subreddits.

    Requires the following environment variables (or pass directly):
    - ``REDDIT_CLIENT_ID``
    - ``REDDIT_CLIENT_SECRET``
    - ``REDDIT_USER_AGENT`` (optional, defaults to a sensible value)

    Parameters
    ----------
    subreddits:
        Override the default subreddit list.
    limit_per_sub:
        Max new posts to pull per subreddit per fetch cycle.
    """

    def __init__(
        self,
        config: FertilitySenseConfig | None = None,
        subreddits: list[str] | None = None,
        limit_per_sub: int = 100,
    ) -> None:
        super().__init__(
            name="reddit",
            source_url="https://www.reddit.com",
            cadence=timedelta(hours=4),
            feed_type="demand",
        )
        if config is None:
            config = FertilitySenseConfig()

        if not config.reddit_client_id:
            raise ValueError(
                "Reddit client ID is required. "
                "Set FERTILITY_SENSE_REDDIT_CLIENT_ID env var or config.reddit_client_id."
            )
        if not config.reddit_client_secret:
            raise ValueError(
                "Reddit client secret is required. "
                "Set FERTILITY_SENSE_REDDIT_CLIENT_SECRET env var or config.reddit_client_secret."
            )

        self.subreddits = subreddits or DEFAULT_SUBREDDITS
        self.limit_per_sub = limit_per_sub
        self._client_id = config.reddit_client_id
        self._client_secret = config.reddit_client_secret
        self._user_agent = config.reddit_user_agent
        self._cached_reddit: praw.Reddit | None = None

    def _reddit(self) -> praw.Reddit:
        """Lazily construct and cache a PRAW Reddit instance."""
        if self._cached_reddit is None:
            self._cached_reddit = praw.Reddit(
                client_id=self._client_id,
                client_secret=self._client_secret,
                user_agent=self._user_agent,
            )
        return self._cached_reddit

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Pull new posts from each subreddit.

        PRAW is synchronous, so this runs in the calling thread.  For a
        production deployment wrap in ``asyncio.to_thread``.
        """
        reddit = self._reddit()
        since_ts = since.timestamp()
        raw: list[dict[str, Any]] = []
        failed_subs: list[str] = []

        for sub_idx, sub_name in enumerate(self.subreddits):
            try:
                subreddit = reddit.subreddit(sub_name)
                for post in subreddit.new(limit=self.limit_per_sub):
                    if post.created_utc < since_ts:
                        continue
                    body = post.selftext or ""
                    combined = f"{post.title} {body}"
                    if not _is_relevant(combined):
                        continue
                    raw.append(
                        {
                            "id": post.id,
                            "subreddit": sub_name,
                            "title": post.title,
                            "selftext": body,
                            "score": post.score,
                            "num_comments": post.num_comments,
                            "created_utc": post.created_utc,
                            "url": f"https://www.reddit.com{post.permalink}",
                        }
                    )
            except Exception:
                failed_subs.append(sub_name)
                logger.exception("Failed to fetch r/%s — continuing with remaining subs", sub_name)

            # Rate-limit between subreddits to respect Reddit's 60 req/min.
            if sub_idx < len(self.subreddits) - 1:
                await asyncio.sleep(_RATE_LIMIT_DELAY_SECONDS)

        if failed_subs:
            logger.warning(
                "Reddit: %d/%d subs failed: %s",
                len(failed_subs),
                len(self.subreddits),
                ", ".join(failed_subs),
            )
        logger.info(
            "Reddit: fetched %d relevant posts across %d subs (%d failed)",
            len(raw),
            len(self.subreddits),
            len(failed_subs),
        )
        return raw

    # ------------------------------------------------------------------
    # Normalize
    # ------------------------------------------------------------------

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Convert raw Reddit posts into ``SignalEvent`` models."""
        signals: list[BaseModel] = []

        for post in raw:
            combined = f"{post['title']} {post.get('selftext', '')}"
            # Volume proxy: upvotes + 2*comments (engagement-weighted).
            volume = max(post.get("score", 0), 0) + 2 * max(post.get("num_comments", 0), 0)
            # Velocity: use comment-to-score ratio as an engagement velocity proxy.
            score = max(post.get("score", 1), 1)
            velocity = round(post.get("num_comments", 0) / score, 4)

            signals.append(
                SignalEvent(
                    signal_id=_signal_id(post["id"]),
                    source=SignalSource.REDDIT,
                    raw_query=post["title"],
                    volume=volume,
                    velocity=velocity,
                    sentiment=_estimate_sentiment(combined),
                    geo="US",  # Reddit is US-dominated; refine with geo inference later.
                    observed_at=datetime.fromtimestamp(
                        post["created_utc"], tz=timezone.utc
                    ),
                    metadata={
                        "subreddit": post["subreddit"],
                        "score": post.get("score"),
                        "num_comments": post.get("num_comments"),
                        "url": post.get("url"),
                    },
                )
            )

        return signals
