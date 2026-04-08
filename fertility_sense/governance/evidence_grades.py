"""Evidence grade definitions and utilities."""

from __future__ import annotations

from fertility_sense.models.evidence import EvidenceGrade


# Grade ordering for comparisons (higher index = stronger)
GRADE_ORDER: dict[EvidenceGrade, int] = {
    EvidenceGrade.D: 0,
    EvidenceGrade.C: 1,
    EvidenceGrade.B: 2,
    EvidenceGrade.A: 3,
    EvidenceGrade.X: 4,  # Special: definitive harm
}

GRADE_LABELS: dict[EvidenceGrade, str] = {
    EvidenceGrade.A: "Strong evidence (systematic review / RCT)",
    EvidenceGrade.B: "Moderate evidence (well-designed observational study)",
    EvidenceGrade.C: "Limited evidence (expert opinion / case series)",
    EvidenceGrade.D: "Weak evidence (anecdotal / conflicting)",
    EvidenceGrade.X: "Contraindicated (known harm)",
}


def grade_meets_minimum(grade: EvidenceGrade, minimum: EvidenceGrade) -> bool:
    """Check if an evidence grade meets or exceeds the minimum threshold."""
    if grade == EvidenceGrade.X:
        return True  # X always qualifies (definitive finding)
    if minimum == EvidenceGrade.X:
        return grade == EvidenceGrade.X
    return GRADE_ORDER[grade] >= GRADE_ORDER[minimum]


def floor_grade(grades: list[EvidenceGrade]) -> EvidenceGrade | None:
    """Return the lowest (weakest) grade from a set, ignoring X."""
    non_x = [g for g in grades if g != EvidenceGrade.X]
    if not non_x:
        return EvidenceGrade.X if grades else None
    return min(non_x, key=lambda g: GRADE_ORDER[g])
