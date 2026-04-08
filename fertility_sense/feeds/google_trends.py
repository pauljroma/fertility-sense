"""Google Trends demand feed.

Polls Google Trends via the ``pytrends`` library for fertility-related
keyword interest over time, converts results to ``SignalEvent`` records.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel

try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None  # type: ignore[misc,assignment]

from fertility_sense.feeds.base import BaseFeed
from fertility_sense.models.signal import SignalEvent, SignalSource

logger = logging.getLogger(__name__)

# Google Trends API allows at most 5 keywords per request.
_BATCH_SIZE = 5

DEFAULT_KEYWORDS: list[str] = [
    "fertility",
    "ovulation",
    "IVF",
    "prenatal vitamins",
    "pregnancy test",
    "egg freezing",
    "sperm count",
    "implantation",
    "luteal phase",
    "basal body temperature",
    "AMH test",
    "PCOS fertility",
    "clomid",
    "IUI",
    "embryo transfer",
]


def _batches(lst: list[str], n: int) -> list[list[str]]:
    """Chunk a list into sublists of at most *n* items."""
    return [lst[i : i + n] for i in range(0, len(lst), n)]


def _signal_id(keyword: str, ts: str, geo: str) -> str:
    """Deterministic ID so we can de-duplicate across runs."""
    raw = f"google_trends:{keyword}:{ts}:{geo}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class GoogleTrendsFeed(BaseFeed):
    """Demand feed sourcing search interest from Google Trends.

    Parameters
    ----------
    keywords:
        Overrides the default keyword list.
    geo:
        ISO-3166 country code. Defaults to ``US``.
    hl:
        Host language for the Trends interface.
    """

    def __init__(
        self,
        keywords: list[str] | None = None,
        geo: str = "US",
        hl: str = "en-US",
    ) -> None:
        super().__init__(
            name="google_trends",
            source_url="https://trends.google.com",
            cadence=timedelta(hours=6),
            feed_type="demand",
        )
        self.keywords = keywords or DEFAULT_KEYWORDS
        self.geo = geo
        self.hl = hl

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Query Google Trends for each keyword batch.

        ``since`` determines the ``timeframe`` parameter passed to pytrends.
        We use the custom short-date format ``YYYY-MM-DD YYYY-MM-DD``.
        """
        now = datetime.now(tz=timezone.utc)
        start_str = since.strftime("%Y-%m-%d")
        end_str = now.strftime("%Y-%m-%d")
        timeframe = f"{start_str} {end_str}"

        pytrends = TrendReq(hl=self.hl, tz=0)
        raw_records: list[dict[str, Any]] = []

        for batch in _batches(self.keywords, _BATCH_SIZE):
            try:
                pytrends.build_payload(
                    kw_list=batch,
                    cat=0,
                    timeframe=timeframe,
                    geo=self.geo,
                )
                iot = pytrends.interest_over_time()
                if iot.empty:
                    logger.debug("Empty response for batch %s", batch)
                    continue

                # Drop the 'isPartial' column if present.
                if "isPartial" in iot.columns:
                    iot = iot.drop(columns=["isPartial"])

                # Convert DataFrame → list of row dicts.
                for ts, row in iot.iterrows():
                    for keyword in batch:
                        if keyword not in row.index:
                            continue
                        raw_records.append(
                            {
                                "keyword": keyword,
                                "timestamp": ts.isoformat(),
                                "value": int(row[keyword]),
                                "geo": self.geo,
                            }
                        )
            except Exception:
                logger.exception("Google Trends batch failed: %s", batch)

        logger.info("GoogleTrends: fetched %d raw data-points", len(raw_records))
        return raw_records

    # ------------------------------------------------------------------
    # Normalize
    # ------------------------------------------------------------------

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Convert raw Trends rows into ``SignalEvent`` models.

        Velocity is approximated as the percentage change between the
        current value and a simple rolling average over the batch.
        """
        if not raw:
            return []

        # Build per-keyword time-series for velocity calculation.
        by_keyword: dict[str, list[dict[str, Any]]] = {}
        for r in raw:
            by_keyword.setdefault(r["keyword"], []).append(r)

        signals: list[BaseModel] = []
        for keyword, rows in by_keyword.items():
            # Sort chronologically.
            rows.sort(key=lambda r: r["timestamp"])
            values = [r["value"] for r in rows]
            mean_value = sum(values) / len(values) if values else 1.0

            for idx, row in enumerate(rows):
                value = row["value"]
                # Velocity: percentage deviation from the series mean.
                velocity = ((value - mean_value) / mean_value) if mean_value else 0.0

                signals.append(
                    SignalEvent(
                        signal_id=_signal_id(keyword, row["timestamp"], row["geo"]),
                        source=SignalSource.GOOGLE_TRENDS,
                        raw_query=keyword,
                        volume=value,
                        velocity=round(velocity, 4),
                        geo=row["geo"],
                        observed_at=datetime.fromisoformat(row["timestamp"]),
                        metadata={
                            "series_mean": round(mean_value, 2),
                            "series_length": len(rows),
                        },
                    )
                )

        return signals
