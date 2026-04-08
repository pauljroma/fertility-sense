"""MotherToBaby evidence + safety feed.

Fetches fact-sheet pages from mothertobaby.org covering medication/exposure
safety during pregnancy and lactation, then normalises each fact sheet
into ``EvidenceRecord`` and ``SafetyAlert`` models.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from pydantic import BaseModel

from fertility_sense.feeds.base import BaseFeed
from fertility_sense.models.evidence import EvidenceGrade, EvidenceRecord
from fertility_sense.models.safety import SafetyAlert, SafetySeverity

logger = logging.getLogger(__name__)

# Be polite: max 2 requests/second to avoid overloading the site.
_SCRAPE_DELAY_SECONDS = 0.5

# The public fact-sheet listing endpoint.
_BASE_URL = "https://mothertobaby.org"
_FACT_SHEET_LIST_URL = f"{_BASE_URL}/fact-sheets/"

# Rough risk-keyword mapping used for severity classification.
_HIGH_RISK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"birth defect", re.IGNORECASE),
    re.compile(r"miscarriage", re.IGNORECASE),
    re.compile(r"stillbirth", re.IGNORECASE),
    re.compile(r"contraindicated", re.IGNORECASE),
    re.compile(r"do not (take|use)", re.IGNORECASE),
]
_MEDIUM_RISK_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"limited (data|studies|information)", re.IGNORECASE),
    re.compile(r"not (enough|sufficient) (data|studies)", re.IGNORECASE),
    re.compile(r"uncertain", re.IGNORECASE),
    re.compile(r"more research needed", re.IGNORECASE),
]


def _fact_sheet_id(title: str) -> str:
    raw = f"mother_to_baby:{title.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _classify_severity(text: str) -> SafetySeverity:
    """Heuristic severity from fact-sheet body text."""
    for pat in _HIGH_RISK_PATTERNS:
        if pat.search(text):
            return SafetySeverity.HIGH
    for pat in _MEDIUM_RISK_PATTERNS:
        if pat.search(text):
            return SafetySeverity.MEDIUM
    return SafetySeverity.LOW


def _classify_grade(text: str) -> EvidenceGrade:
    """Heuristic evidence grade from fact-sheet body text."""
    lower = text.lower()
    if "systematic review" in lower or "randomized" in lower or "meta-analysis" in lower:
        return EvidenceGrade.A
    if "cohort" in lower or "case-control" in lower or "registry" in lower:
        return EvidenceGrade.B
    if "case report" in lower or "case series" in lower or "expert" in lower:
        return EvidenceGrade.C
    return EvidenceGrade.D


def _extract_substances(title: str, text: str) -> list[str]:
    """Pull substance names from the fact sheet.

    The title almost always *is* the substance name.  We also look for
    parenthetical brand names, e.g. ``Acetaminophen (Tylenol)``.
    """
    substances: list[str] = []
    # Title itself is the primary substance.
    clean_title = re.sub(r"\s*\(.*?\)", "", title).strip()
    if clean_title:
        substances.append(clean_title)
    # Parenthetical brand names in the title.
    brands = re.findall(r"\(([^)]+)\)", title)
    substances.extend(brands)
    return substances


def _extract_key_findings(text: str) -> list[str]:
    """Pull bullet-point style key findings from the text."""
    findings: list[str] = []
    # Look for sentences that start with common summary patterns.
    patterns = [
        r"(?:studies?\s+(?:show|found|suggest))[^.]+\.",
        r"(?:there is\s+(?:no|some|limited|increased))[^.]+\.",
        r"(?:the risk\s+(?:of|for))[^.]+\.",
    ]
    for pat in patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            finding = match.group(0).strip()
            if finding and finding not in findings:
                findings.append(finding)
    return findings[:5]  # Cap at 5 findings.


def _action_for_severity(severity: SafetySeverity) -> str:
    mapping = {
        SafetySeverity.CRITICAL: "withdraw_content",
        SafetySeverity.HIGH: "add_warning",
        SafetySeverity.MEDIUM: "monitor",
        SafetySeverity.LOW: "none",
    }
    return mapping[severity]


class MotherToBabyFeed(BaseFeed):
    """Evidence + Safety feed sourcing fact sheets from MotherToBaby.

    MotherToBaby (a service of the Organization of Teratology Information
    Specialists) publishes peer-reviewed fact sheets covering medication
    and chemical exposures during pregnancy and breastfeeding.
    """

    def __init__(self) -> None:
        super().__init__(
            name="mother_to_baby",
            source_url=_BASE_URL,
            cadence=timedelta(days=7),
            feed_type="evidence",  # Also produces safety alerts.
        )

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    async def fetch_raw(self, since: datetime) -> list[dict[str, Any]]:
        """Scrape the fact-sheet listing and individual pages.

        1. GET the listing page and extract fact-sheet links.
        2. For each link, GET the detail page and extract the body text.

        The ``since`` parameter is used to skip fact sheets whose page
        content hasn't changed (based on a header check), but since
        MotherToBaby doesn't expose modification dates via headers, we
        always re-fetch the full list on a weekly cadence.
        """
        raw_sheets: list[dict[str, Any]] = []

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0),
            follow_redirects=True,
            headers={"User-Agent": "FertilitySense/0.1 (+https://fertilitysense.dev)"},
        ) as client:
            # Step 1: Get listing page.
            try:
                listing_resp = await client.get(_FACT_SHEET_LIST_URL)
                listing_resp.raise_for_status()
            except httpx.HTTPError:
                logger.exception("Failed to fetch MotherToBaby listing page")
                return []

            listing_html = listing_resp.text

            # Extract fact-sheet links — they follow the pattern /fact-sheets/<slug>/
            links = re.findall(
                r'href="(/fact-sheets/[a-z0-9_-]+/?)"',
                listing_html,
                re.IGNORECASE,
            )
            # Deduplicate while preserving order.
            seen: set[str] = set()
            unique_links: list[str] = []
            for link in links:
                normalised = link.rstrip("/")
                if normalised not in seen:
                    seen.add(normalised)
                    unique_links.append(link)

            logger.info("MotherToBaby: found %d fact-sheet links", len(unique_links))

            # Step 2: Fetch each detail page with rate limiting.
            failed_sheets = 0
            for sheet_idx, link in enumerate(unique_links):
                url = f"{_BASE_URL}{link}" if link.startswith("/") else link
                try:
                    detail_resp = await client.get(url)
                    detail_resp.raise_for_status()
                except httpx.HTTPError:
                    failed_sheets += 1
                    logger.warning("Failed to fetch fact sheet: %s", url)
                    continue
                except Exception:
                    failed_sheets += 1
                    logger.warning("Unexpected error fetching fact sheet: %s", url)
                    continue

                html = detail_resp.text

                # Extract <title> as the fact-sheet title.
                title_match = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
                title = title_match.group(1).strip() if title_match else link

                # Strip HTML tags for a rough plain-text body.
                body = re.sub(r"<[^>]+>", " ", html)
                body = re.sub(r"\s+", " ", body).strip()

                raw_sheets.append(
                    {
                        "title": title,
                        "url": url,
                        "body": body[:10000],  # Cap at 10k chars to limit memory.
                    }
                )

                # Rate-limit to be polite (max 2 req/sec).
                if sheet_idx < len(unique_links) - 1:
                    await asyncio.sleep(_SCRAPE_DELAY_SECONDS)

            if failed_sheets:
                logger.warning(
                    "MotherToBaby: %d/%d fact sheets failed to fetch",
                    failed_sheets,
                    len(unique_links),
                )

        logger.info("MotherToBaby: fetched %d fact sheets", len(raw_sheets))
        return raw_sheets

    # ------------------------------------------------------------------
    # Normalize
    # ------------------------------------------------------------------

    def normalize(self, raw: list[dict[str, Any]]) -> list[BaseModel]:
        """Produce both ``EvidenceRecord`` and ``SafetyAlert`` per sheet."""
        records: list[BaseModel] = []

        for sheet in raw:
            title = sheet["title"]
            body = sheet.get("body", "")
            url = sheet["url"]
            fid = _fact_sheet_id(title)

            substances = _extract_substances(title, body)
            grade = _classify_grade(body)
            severity = _classify_severity(body)
            key_findings = _extract_key_findings(body)

            # Evidence record.
            records.append(
                EvidenceRecord(
                    evidence_id=f"ev-{fid}",
                    source_feed="mother_to_baby",
                    title=title,
                    abstract=body[:500] if body else None,
                    url=url,
                    grade=grade,
                    grade_rationale=f"Auto-graded from MotherToBaby fact sheet text (heuristic: {grade.value})",
                    topics=[s.lower().replace(" ", "_") for s in substances],
                    key_findings=key_findings,
                    population="pregnant and lactating individuals",
                )
            )

            # Safety alert (only if severity >= MEDIUM).
            if severity in (SafetySeverity.CRITICAL, SafetySeverity.HIGH, SafetySeverity.MEDIUM):
                records.append(
                    SafetyAlert(
                        alert_id=f"sa-{fid}",
                        source="mother_to_baby",
                        title=f"Exposure alert: {title}",
                        severity=severity,
                        affected_substances=substances,
                        affected_topics=[s.lower().replace(" ", "_") for s in substances],
                        description=body[:300] if body else "See fact sheet for details.",
                        action_required=_action_for_severity(severity),
                        url=url,
                        published_at=datetime.now(tz=timezone.utc),
                    )
                )

        return records
