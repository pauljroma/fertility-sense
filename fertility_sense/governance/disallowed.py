"""Disallowed answer classes — content that must never be generated.

Patterns are loaded from ``data/governance/disallowed_patterns.yaml`` when
available, with a hardcoded fallback for resilience.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Resolve YAML path relative to project root (two levels up from this file)
_DEFAULT_YAML_PATH = Path(__file__).resolve().parents[2] / "data" / "governance" / "disallowed_patterns.yaml"


@dataclass(frozen=True)
class DisallowedPattern:
    name: str
    description: str
    patterns: list[str]
    replacement_text: str


# ---------------------------------------------------------------------------
# Hardcoded fallback (used when YAML file is missing)
# ---------------------------------------------------------------------------

_FALLBACK_CLASSES: list[DisallowedPattern] = [
    DisallowedPattern(
        name="diagnosis",
        description="Never state a diagnosis",
        patterns=[
            r"you have \w+",
            r"you are diagnosed with",
            r"this means you have",
            r"you(?:'re| are) suffering from",
            r"you likely have",
            r"this indicates you have",
            r"based on this you're",
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
            r"recommended amount is",
            r"optimal dose",
            r"take \d+ daily",
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
            r"it's nothing serious",
            r"don't worry about",
            r"you can safely ignore",
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
            r"proven to work every time",
            r"always results in",
            r"never fails to",
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
            r"doctors just want to",
            r"medicine doesn't work for",
            r"natural is better than",
        ],
        replacement_text="We recommend discussing your concerns with a "
        "qualified healthcare provider.",
    ),
    DisallowedPattern(
        name="false_equivalence",
        description="Never equate unproven remedies with medical treatments",
        patterns=[
            r"just as good as",
            r"equivalent to (?:IVF|medication|treatment|surgery|therapy)",
            r"works the same as",
            r"a natural alternative to (?:IVF|medication|treatment|surgery)",
            r"replaces the need for",
        ],
        replacement_text="Alternative approaches have not been shown to be equivalent to "
        "established medical treatments. Discuss all options with your provider.",
    ),
    DisallowedPattern(
        name="unproven_claims",
        description="Never assert clinical proof without citation",
        patterns=[
            r"clinically proven to",
            r"scientifically shown that",
            r"studies prove that",
            r"research confirms that",
            r"medical evidence shows",
        ],
        replacement_text="Claims about clinical evidence should be verified with your "
        "healthcare provider and peer-reviewed sources.",
    ),
]

# ---------------------------------------------------------------------------
# YAML loading
# ---------------------------------------------------------------------------


def _load_from_yaml(path: Path) -> list[DisallowedPattern]:
    """Parse the YAML file into DisallowedPattern instances."""
    data = yaml.safe_load(path.read_text())
    classes: list[DisallowedPattern] = []
    for entry in data["disallowed_classes"]:
        classes.append(
            DisallowedPattern(
                name=entry["name"],
                description=entry["description"],
                patterns=entry["patterns"],
                replacement_text=entry["replacement_text"],
            )
        )
    return classes


def _load_classes(yaml_path: Path = _DEFAULT_YAML_PATH) -> list[DisallowedPattern]:
    """Load disallowed classes from YAML, falling back to hardcoded."""
    try:
        if yaml_path.exists():
            classes = _load_from_yaml(yaml_path)
            logger.info("Loaded %d disallowed pattern classes from %s", len(classes), yaml_path)
            return classes
    except Exception:
        logger.warning("Failed to load disallowed patterns from %s, using fallback", yaml_path, exc_info=True)
    return list(_FALLBACK_CLASSES)


# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

DISALLOWED_CLASSES: list[DisallowedPattern] = _load_classes()

_COMPILED_PATTERNS: list[tuple[DisallowedPattern, list[re.Pattern[str]]]] | None = None


def _compile_patterns() -> list[tuple[DisallowedPattern, list[re.Pattern[str]]]]:
    global _COMPILED_PATTERNS
    if _COMPILED_PATTERNS is None:
        _COMPILED_PATTERNS = [
            (dc, [re.compile(p, re.IGNORECASE) for p in dc.patterns])
            for dc in DISALLOWED_CLASSES
        ]
    return _COMPILED_PATTERNS


def reload_patterns(yaml_path: Path = _DEFAULT_YAML_PATH) -> int:
    """Reload patterns from YAML (hot-reload). Returns count of classes loaded."""
    global DISALLOWED_CLASSES, _COMPILED_PATTERNS
    DISALLOWED_CLASSES = _load_classes(yaml_path)
    _COMPILED_PATTERNS = None  # force recompilation
    return len(DISALLOWED_CLASSES)


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
