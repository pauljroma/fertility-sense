"""Competitor intelligence feed for WIN Fertility.

Tracks WIN's key competitors in the fertility benefits space with
static intelligence profiles. Each competitor entry includes revenue
estimates, client counts, strengths/weaknesses, and WIN's positioning.

Data source: Static intelligence (will integrate news APIs later)
Cadence: 7 days
Type: intelligence
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel

from fertility_sense.feeds.base import BaseFeed
from fertility_sense.models.evidence import EvidenceGrade, EvidenceRecord

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Competitor database
# ---------------------------------------------------------------------------

COMPETITORS: dict[str, dict[str, Any]] = {
    "progyny": {
        "name": "Progyny",
        "type": "fertility_benefits_manager",
        "public": True,  # NASDAQ: PGNY
        "est_revenue": "$1.1B (2025)",
        "est_clients": "400+ employers",
        "strengths": [
            "Large provider network",
            "Public company scale",
            "Insurance carrier partnerships",
        ],
        "weaknesses": [
            "Higher cost per cycle",
            "Less flexible for small employers",
            "Cookie-cutter network",
        ],
        "win_positioning": (
            "WIN delivers comparable outcomes at 20-30% lower cost "
            "through tighter network management and drug company negotiations"
        ),
    },
    "carrot": {
        "name": "Carrot Fertility",
        "type": "fertility_navigation",
        "public": False,
        "est_revenue": "$200M+ (2025)",
        "est_clients": "1000+ employers (but smaller)",
        "strengths": [
            "Tech-forward UX",
            "Global coverage",
            "Inclusive (LGBTQ+, single parents)",
        ],
        "weaknesses": [
            "Navigation-only (no managed network)",
            "Less clinical depth",
            "Higher per-employee cost for comprehensive coverage",
        ],
        "win_positioning": (
            "WIN manages the full clinical journey with negotiated provider "
            "rates — not just navigation and reimbursement"
        ),
    },
    "maven": {
        "name": "Maven Clinic",
        "type": "virtual_clinic",
        "public": False,
        "est_revenue": "$150M+ (2025)",
        "est_clients": "200+ employers",
        "strengths": [
            "Virtual-first model",
            "Broader women's health",
            "Strong brand",
        ],
        "weaknesses": [
            "Primarily virtual — limited in-person network",
            "Diluted fertility focus (maternity/postpartum too)",
            "Less cost management",
        ],
        "win_positioning": (
            "WIN is purpose-built for fertility with a managed in-person "
            "provider network — not a virtual clinic bolting on benefits management"
        ),
    },
    "kindbody": {
        "name": "Kindbody",
        "type": "owned_clinics",
        "public": False,
        "est_revenue": "$100M+ (2025)",
        "est_clients": "100+ employers",
        "strengths": [
            "Own clinics = full control",
            "Modern patient experience",
            "Egg freezing brand",
        ],
        "weaknesses": [
            "Limited geography (own clinics only)",
            "High capex model",
            "Can't scale to rural/distributed workforces",
        ],
        "win_positioning": (
            "WIN's network model covers any geography without building "
            "clinics — better for distributed workforces"
        ),
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_competitor(name: str) -> dict[str, Any] | None:
    """Return competitor profile by key (lowercase), or None if not found."""
    key = name.lower().replace(" ", "_")
    # Try exact match first, then search by display name
    if key in COMPETITORS:
        return COMPETITORS[key]
    for k, v in COMPETITORS.items():
        if v["name"].lower() == name.lower():
            return v
    return None


def win_vs_competitor(name: str) -> str | None:
    """Return WIN's positioning statement against a named competitor."""
    comp = get_competitor(name)
    if comp is None:
        return None
    return comp["win_positioning"]


def _competitor_evidence_id(key: str) -> str:
    """Deterministic evidence ID for a competitor profile."""
    raw = f"competitor_intel:{key}"
    return f"ev-ci-{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


# ---------------------------------------------------------------------------
# Feed class
# ---------------------------------------------------------------------------


class CompetitorIntelFeed(BaseFeed):
    """Intelligence feed tracking WIN Fertility's competitive landscape.

    Each competitor profile is converted to an EvidenceRecord that the
    sales team can use for positioning and battlecard preparation.

    Currently uses a hardcoded database. A future version will integrate
    with news APIs (e.g., NewsAPI, Google News) to detect competitor
    funding rounds, client announcements, and leadership changes.
    """

    def __init__(self) -> None:
        super().__init__(
            name="competitor_intel",
            source_url="https://www.google.com/search?q=fertility+benefits+competitor+news",
            cadence=timedelta(days=7),
            feed_type="intelligence",
        )

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Return the hardcoded competitor database.

        TODO: Integrate news API to pull recent competitor mentions,
        funding announcements, and client wins/losses.
        """
        raw: list[dict[str, Any]] = []
        for key, info in COMPETITORS.items():
            raw.append({"key": key, **info})
        logger.info("CompetitorIntelFeed: returning %d competitor profiles", len(raw))
        return raw

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Convert competitor profiles to EvidenceRecord objects.

        Each competitor becomes a citable intelligence record for WIN's
        sales team, graded C (industry intelligence / expert analysis).
        """
        records: list[BaseModel] = []

        for comp in raw:
            key = comp["key"]
            name = comp["name"]
            comp_type = comp["type"].replace("_", " ").title()
            revenue = comp["est_revenue"]
            clients = comp["est_clients"]
            strengths = comp["strengths"]
            weaknesses = comp["weaknesses"]
            positioning = comp["win_positioning"]

            title = f"Competitive Intel: {name} ({comp_type}) — {revenue}"

            findings = [
                f"{name}: {revenue} revenue, {clients}.",
                f"Strengths: {', '.join(strengths)}.",
                f"Weaknesses: {', '.join(weaknesses)}.",
                f"WIN positioning: {positioning}.",
            ]

            topics = ["competitive-landscape", "fertility-benefits"]
            if comp.get("public"):
                topics.append("public-company-competitor")

            records.append(
                EvidenceRecord(
                    evidence_id=_competitor_evidence_id(key),
                    source_feed="competitor_intel",
                    title=title,
                    abstract=(
                        f"{name} is a {comp_type.lower()} with estimated {revenue} "
                        f"revenue and {clients}. "
                        f"WIN positioning: {positioning}"
                    ),
                    url=f"https://www.google.com/search?q={name.replace(' ', '+')}+fertility+benefits",
                    grade=EvidenceGrade.C,
                    grade_rationale="Industry intelligence — expert analysis of publicly available information",
                    topics=topics,
                    key_findings=findings,
                )
            )

        return records
