"""US state fertility treatment mandate tracker feed.

Tracks state-level laws requiring insurance coverage for fertility
treatment. WIN Fertility uses this data to:
1. Identify states where employers MUST offer fertility coverage (sales trigger)
2. Alert when new mandates pass (pipeline opportunity)
3. Support compliance arguments in sales materials

Data source: NCSL / state legislature records (hardcoded for now)
Cadence: 30 days
Type: regulatory
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
# Current US state fertility mandates (as of 2026)
# ---------------------------------------------------------------------------

STATE_MANDATES: dict[str, dict[str, Any]] = {
    "AR": {
        "type": "mandate_to_cover",
        "since": 1987,
        "ivf_covered": True,
        "details": "HB 1389 - IVF coverage required for groups 25+",
    },
    "CA": {
        "type": "mandate_to_cover",
        "since": 2024,
        "ivf_covered": True,
        "details": "SB 729 - Comprehensive fertility coverage including IVF",
    },
    "CO": {
        "type": "mandate_to_cover",
        "since": 2022,
        "ivf_covered": True,
        "details": "HB 22-1008 - Building Families Act",
    },
    "CT": {
        "type": "mandate_to_cover",
        "since": 2005,
        "ivf_covered": True,
        "details": "PA 05-196 - IVF mandate for insured groups",
    },
    "DE": {
        "type": "mandate_to_cover",
        "since": 2018,
        "ivf_covered": True,
        "details": "SB 139 - Fertility coverage mandate",
    },
    "HI": {
        "type": "mandate_to_cover",
        "since": 1987,
        "ivf_covered": True,
        "details": "HB 2450 - One IVF cycle per lifetime",
    },
    "IL": {
        "type": "mandate_to_cover",
        "since": 1991,
        "ivf_covered": True,
        "details": "PA 91-0660 - Comprehensive fertility mandate",
    },
    "LA": {
        "type": "mandate_to_offer",
        "since": 2001,
        "ivf_covered": False,
        "details": "HB 967 - Must offer, IVF excluded",
    },
    "MA": {
        "type": "mandate_to_cover",
        "since": 2010,
        "ivf_covered": True,
        "details": "Comprehensive fertility mandate",
    },
    "MD": {
        "type": "mandate_to_cover",
        "since": 2000,
        "ivf_covered": True,
        "details": "SB 486 - IVF after 2 years trying",
    },
    "ME": {
        "type": "mandate_to_cover",
        "since": 2022,
        "ivf_covered": True,
        "details": "LD 1539 - Fertility preservation + IVF",
    },
    "MT": {
        "type": "mandate_to_cover",
        "since": 1987,
        "ivf_covered": False,
        "details": "HB 471 - Fertility but not IVF",
    },
    "NH": {
        "type": "mandate_to_cover",
        "since": 2020,
        "ivf_covered": True,
        "details": "HB 1578 - Fertility coverage mandate",
    },
    "NJ": {
        "type": "mandate_to_cover",
        "since": 2001,
        "ivf_covered": True,
        "details": "S1971 - Comprehensive fertility mandate",
    },
    "NY": {
        "type": "mandate_to_cover",
        "since": 2020,
        "ivf_covered": True,
        "details": "S3070 - 3 IVF cycles required",
    },
    "OH": {
        "type": "mandate_to_offer",
        "since": 1991,
        "ivf_covered": False,
        "details": "HB 135 - Must offer diagnosis coverage",
    },
    "RI": {
        "type": "mandate_to_cover",
        "since": 2017,
        "ivf_covered": True,
        "details": "S0409 - Fertility preservation mandate",
    },
    "TX": {
        "type": "mandate_to_offer",
        "since": 1987,
        "ivf_covered": True,
        "details": "HB 2577 - Must offer IVF coverage",
    },
    "UT": {
        "type": "mandate_to_cover",
        "since": 2022,
        "ivf_covered": True,
        "details": "HB 313 - Fertility preservation",
    },
    "WV": {
        "type": "mandate_to_cover",
        "since": 1977,
        "ivf_covered": False,
        "details": "Fertility diagnosis coverage only",
    },
}

# Full state names for display.
_STATE_NAMES: dict[str, str] = {
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "HI": "Hawaii",
    "IL": "Illinois",
    "LA": "Louisiana",
    "MA": "Massachusetts",
    "MD": "Maryland",
    "ME": "Maine",
    "MT": "Montana",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NY": "New York",
    "OH": "Ohio",
    "RI": "Rhode Island",
    "TX": "Texas",
    "UT": "Utah",
    "WV": "West Virginia",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def mandates_for_state(state_code: str) -> dict[str, Any] | None:
    """Return mandate info for a single state, or None if no mandate exists."""
    code = state_code.upper()
    mandate = STATE_MANDATES.get(code)
    if mandate is None:
        return None
    return {
        "state": code,
        "state_name": _STATE_NAMES.get(code, code),
        **mandate,
    }


def states_with_ivf_mandate() -> list[str]:
    """Return state codes where IVF coverage is mandated or must be offered."""
    return sorted(
        code
        for code, info in STATE_MANDATES.items()
        if info["ivf_covered"]
    )


def _mandate_evidence_id(state_code: str) -> str:
    """Deterministic evidence ID for a state mandate."""
    raw = f"state_mandate:{state_code.lower()}"
    return f"ev-sm-{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


# ---------------------------------------------------------------------------
# Feed class
# ---------------------------------------------------------------------------


class StateMandateFeed(BaseFeed):
    """Regulatory feed tracking US state fertility treatment mandates.

    Each mandate is converted to an EvidenceRecord that WIN's sales team
    can cite: "In [state], employers with 25+ employees must cover IVF."

    Currently uses a hardcoded database of known mandates. A future
    version will scrape NCSL (National Conference of State Legislatures)
    for real-time updates.
    """

    def __init__(self) -> None:
        super().__init__(
            name="state_mandates",
            source_url="https://www.ncsl.org/health/state-laws-related-to-insurance-coverage-for-infertility-treatment",
            cadence=timedelta(days=30),
            feed_type="regulatory",
        )

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Return the hardcoded mandate database.

        TODO: Scrape NCSL for real-time mandate tracking, diff against
        previous snapshot, and flag new/changed mandates.
        """
        raw: list[dict[str, Any]] = []
        for code, info in STATE_MANDATES.items():
            raw.append({
                "state": code,
                "state_name": _STATE_NAMES.get(code, code),
                **info,
            })
        logger.info("StateMandateFeed: returning %d state mandates", len(raw))
        return raw

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Convert state mandate records to EvidenceRecord objects.

        Each mandate becomes a citable piece of evidence for WIN's sales
        team, graded B (well-documented legislative record).
        """
        records: list[BaseModel] = []

        for mandate in raw:
            state = mandate["state"]
            state_name = mandate["state_name"]
            mandate_type = mandate["type"]
            ivf = mandate["ivf_covered"]
            since_year = mandate["since"]
            details = mandate["details"]

            # Build a sales-oriented title
            ivf_str = "including IVF" if ivf else "excluding IVF"
            type_str = "requires coverage" if mandate_type == "mandate_to_cover" else "must offer"
            title = f"{state_name} ({state}): {type_str} for fertility treatment, {ivf_str}"

            # Key findings tailored for B2B sales context
            findings = [
                f"{state_name} has a {mandate_type.replace('_', ' ')} mandate since {since_year}.",
                f"IVF coverage: {'Required' if ivf else 'Not required'}.",
                details,
            ]
            if mandate_type == "mandate_to_cover" and ivf:
                findings.append(
                    f"Sales trigger: Employers in {state_name} with insured employees "
                    f"MUST provide IVF coverage — WIN can be the benefit manager."
                )

            records.append(
                EvidenceRecord(
                    evidence_id=_mandate_evidence_id(state),
                    source_feed="state_mandates",
                    title=title,
                    abstract=(
                        f"State mandate in {state_name}: {details}. "
                        f"Mandate type: {mandate_type.replace('_', ' ')}. "
                        f"IVF covered: {'Yes' if ivf else 'No'}. "
                        f"In effect since {since_year}."
                    ),
                    url=f"https://www.ncsl.org/health/state-laws-related-to-insurance-coverage-for-infertility-treatment#{state.lower()}",
                    grade=EvidenceGrade.B,
                    grade_rationale="State legislative record — well-documented public law",
                    topics=["fertility-insurance-mandates", "ivf-coverage", "employer-benefits"],
                    key_findings=findings,
                    population=f"Insured employees in {state_name}",
                )
            )

        return records
