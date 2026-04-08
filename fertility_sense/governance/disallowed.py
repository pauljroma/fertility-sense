"""Disallowed answer classes — content that must never be generated."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class DisallowedPattern:
    name: str
    description: str
    patterns: list[str]
    replacement_text: str


DISALLOWED_CLASSES: list[DisallowedPattern] = [
    DisallowedPattern(
        name="diagnosis",
        description="Never state a diagnosis",
        patterns=[
            r"you have \w+",
            r"you are diagnosed with",
            r"this means you have",
            r"you(?:'re| are) suffering from",
        ],
        replacement_text="Symptoms may be associated with [condition]. "
        "Please consult your healthcare provider for a proper evaluation.",
    ),
    DisallowedPattern(
        name="dosage",
        description="Never recommend specific drug dosages",
        patterns=[
            r"take \d+ ?mg",
            r"dose of \d+",
            r"recommended dose is",
            r"you should take \d+",
        ],
        replacement_text="Dosage should be determined by your healthcare provider "
        "based on your individual needs.",
    ),
    DisallowedPattern(
        name="emergency_triage",
        description="Never triage emergency symptoms without ER direction",
        patterns=[
            r"you (?:don't|do not) need to go to",
            r"this is (?:probably )?not an emergency",
            r"wait and see if",
            r"no need to call (?:your doctor|911)",
        ],
        replacement_text="If you are experiencing concerning symptoms, "
        "call 911 or go to your nearest emergency room immediately.",
    ),
    DisallowedPattern(
        name="outcome_guarantee",
        description="Never guarantee outcomes",
        patterns=[
            r"you will (?:definitely|certainly|surely)",
            r"guaranteed to",
            r"100% (?:success|effective|safe)",
            r"this will cure",
        ],
        replacement_text="Results vary by individual. "
        "Discuss expected outcomes with your healthcare provider.",
    ),
    DisallowedPattern(
        name="anti_medical",
        description="Never discourage professional care",
        patterns=[
            r"you don't need (?:a |to see a )?doctor",
            r"skip (?:your|the) (?:doctor|appointment)",
            r"doctors (?:don't know|are wrong)",
            r"instead of seeing a doctor",
        ],
        replacement_text="We recommend discussing your concerns with a "
        "qualified healthcare provider.",
    ),
]

_COMPILED_PATTERNS: list[tuple[DisallowedPattern, list[re.Pattern[str]]]] | None = None


def _compile_patterns() -> list[tuple[DisallowedPattern, list[re.Pattern[str]]]]:
    global _COMPILED_PATTERNS
    if _COMPILED_PATTERNS is None:
        _COMPILED_PATTERNS = [
            (dc, [re.compile(p, re.IGNORECASE) for p in dc.patterns])
            for dc in DISALLOWED_CLASSES
        ]
    return _COMPILED_PATTERNS


def check_disallowed(text: str) -> list[tuple[str, str, str]]:
    """Check text for disallowed content patterns.

    Returns list of (class_name, matched_text, replacement_text) tuples.
    """
    violations: list[tuple[str, str, str]] = []
    for dc, compiled in _compile_patterns():
        for pattern in compiled:
            match = pattern.search(text)
            if match:
                violations.append((dc.name, match.group(0), dc.replacement_text))
    return violations
