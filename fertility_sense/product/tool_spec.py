"""Interactive tool specification from demand signals."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ToolSpec:
    name: str
    description: str
    tool_type: str  # "calculator", "tracker", "quiz", "checker"
    inputs: list[dict[str, str]] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    evidence_backing: list[str] = field(default_factory=list)
    journey_stages: list[str] = field(default_factory=list)


# Pre-defined tool templates for common fertility/prenatal use cases
TOOL_TEMPLATES: list[ToolSpec] = [
    ToolSpec(
        name="Due Date Calculator",
        description="Calculate estimated due date from LMP or conception date",
        tool_type="calculator",
        inputs=[
            {"name": "lmp_date", "type": "date", "label": "Last Menstrual Period"},
            {"name": "cycle_length", "type": "int", "label": "Average Cycle Length (days)"},
        ],
        outputs=["estimated_due_date", "current_week", "trimester"],
        journey_stages=["pregnancy_t1"],
    ),
    ToolSpec(
        name="Ovulation Predictor",
        description="Predict fertile window based on cycle data",
        tool_type="calculator",
        inputs=[
            {"name": "lmp_date", "type": "date", "label": "Last Period Start Date"},
            {"name": "cycle_length", "type": "int", "label": "Average Cycle Length"},
        ],
        outputs=["fertile_window_start", "fertile_window_end", "estimated_ovulation"],
        journey_stages=["trying", "preconception"],
    ),
    ToolSpec(
        name="Medication Safety Checker",
        description="Check pregnancy/breastfeeding safety of a medication",
        tool_type="checker",
        inputs=[
            {"name": "medication_name", "type": "text", "label": "Medication Name"},
            {"name": "stage", "type": "select", "label": "Pregnancy/Breastfeeding Stage"},
        ],
        outputs=["safety_category", "evidence_summary", "alternatives", "consult_provider_note"],
        evidence_backing=["mother_to_baby", "fda_pllr"],
        journey_stages=["pregnancy_t1", "pregnancy_t2", "pregnancy_t3", "lactation"],
    ),
    ToolSpec(
        name="IVF Success Estimator",
        description="Estimate IVF success rates based on patient factors",
        tool_type="calculator",
        inputs=[
            {"name": "age", "type": "int", "label": "Patient Age"},
            {"name": "diagnosis", "type": "select", "label": "Primary Diagnosis"},
            {"name": "previous_cycles", "type": "int", "label": "Previous IVF Cycles"},
        ],
        outputs=["estimated_success_rate", "national_average", "factors_explanation"],
        evidence_backing=["cdc_art_nass"],
        journey_stages=["fertility_treatment"],
    ),
]
