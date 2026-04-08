"""Prometheus metrics for pipeline observability."""

from __future__ import annotations

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )

    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False

# Metrics (only created if prometheus_client available)
if HAS_PROMETHEUS:
    FEED_INGEST_DURATION = Histogram(
        "fs_feed_ingest_seconds",
        "Feed ingestion duration",
        ["feed_name", "feed_type"],
    )
    FEED_INGEST_RECORDS = Counter(
        "fs_feed_ingest_records_total",
        "Records ingested",
        ["feed_name"],
    )
    FEED_INGEST_ERRORS = Counter(
        "fs_feed_ingest_errors_total",
        "Feed ingestion errors",
        ["feed_name"],
    )

    SCORING_DURATION = Histogram(
        "fs_scoring_seconds",
        "TOS scoring duration",
        ["topic_id"],
    )

    GOVERNANCE_DECISIONS = Counter(
        "fs_governance_decisions_total",
        "Governance gate decisions",
        ["risk_tier", "decision"],
    )

    ASSEMBLY_DURATION = Histogram(
        "fs_assembly_seconds",
        "Answer assembly duration",
    )

    AGENT_CALLS = Counter(
        "fs_agent_calls_total",
        "Claude API calls",
        ["agent_name", "model"],
    )
    AGENT_COST = Counter(
        "fs_agent_cost_usd_total",
        "Claude API cost in USD",
        ["agent_name"],
    )
    AGENT_TOKENS = Counter(
        "fs_agent_tokens_total",
        "Tokens used",
        ["agent_name", "direction"],
    )


def get_metrics_response() -> bytes:
    """Return Prometheus metrics as bytes for the /metrics endpoint."""
    if not HAS_PROMETHEUS:
        return b"# prometheus_client not installed\n"
    return generate_latest()
