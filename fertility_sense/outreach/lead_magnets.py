"""Lead magnet generator — evidence-backed fertility guides via Claude.

Generates downloadable content assets (checklists, guides, cost breakdowns)
that serve as lead magnets for people struggling with fertility.  Each guide
is produced as a Markdown file in ``data/lead_magnets/{name}.md``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fertility_sense.pipeline import Pipeline

logger = logging.getLogger(__name__)


LEAD_MAGNETS: dict[str, dict[str, str]] = {
    "fertility-checklist": {
        "title": "Complete Fertility Diagnostic Checklist",
        "description": "Every test you need before your first consultation",
        "prompt": (
            "Create a comprehensive fertility diagnostic checklist for someone about to "
            "start their fertility journey.  Organise it by category:\n\n"
            "**Blood Work** — FSH (day 3), AMH, estradiol, prolactin, TSH/free T4, "
            "progesterone (day 21), LH, testosterone, DHEA-S, fasting insulin/glucose.\n"
            "For each test: what it measures, when in the cycle to do it, normal reference "
            "ranges, what abnormal results may indicate, and estimated out-of-pocket cost.\n\n"
            "**Imaging** — Transvaginal ultrasound (antral follicle count), "
            "hysterosalpingography (HSG), sonohysterogram, MRI (when indicated).\n"
            "For each: what it evaluates, prep required, what to expect, cost.\n\n"
            "**Male Partner** — Semen analysis (volume, count, motility, morphology), "
            "DNA fragmentation, hormone panel (FSH, testosterone, prolactin).\n\n"
            "**Genetic Screening** — Carrier screening, karyotype, Y-chromosome "
            "microdeletion (when indicated).\n\n"
            "**Lifestyle Assessment** — BMI, caffeine/alcohol intake, medication review, "
            "environmental exposures.\n\n"
            "Format as a printable checklist with checkboxes.  Grade each test by evidence "
            "level (A = strong RCT evidence, B = cohort/observational, C = expert consensus). "
            "Include a 'Questions to ask your RE' section at the end.  "
            "Cite ASRM/ESHRE guidelines where applicable."
        ),
    },
    "ivf-cost-guide": {
        "title": "The Real Cost of IVF",
        "description": "Complete breakdown of IVF costs by region, clinic, and insurance",
        "prompt": (
            "Create a detailed IVF cost breakdown guide for US patients.  Cover:\n\n"
            "**Base IVF Cycle Costs** — Monitoring (blood + ultrasound), egg retrieval, "
            "anesthesia, embryo culture, fresh transfer.  National average and range.\n\n"
            "**Medications** — Gonadotropins (Gonal-F, Menopur, Follistim), trigger shots "
            "(Ovidrel, Lupron), progesterone support.  Brand vs generic, pharmacy savings, "
            "manufacturer discount programs.\n\n"
            "**Add-Ons** — ICSI, PGT-A/PGT-M, assisted hatching, embryo glue, "
            "endometrial receptivity testing (ERA).  Evidence grade for each add-on "
            "(strong evidence vs unproven).\n\n"
            "**Frozen Embryo Transfer (FET)** — Storage fees, thaw cycle monitoring, "
            "transfer costs.\n\n"
            "**Regional Variation** — Cost ranges for Northeast, Southeast, Midwest, "
            "West Coast, Texas/Florida.  Top 5 most affordable metro areas.\n\n"
            "**Insurance** — States with fertility mandates (list all), employer-sponsored "
            "benefits (Progyny, Carrot, WINFertility), FSA/HSA strategies, "
            "clinical trial options.\n\n"
            "**Hidden Costs** — Time off work, travel for monitoring, emotional support/"
            "therapy, supplements, acupuncture.\n\n"
            "**Cost-Saving Strategies** — Shared-risk/refund programs, mini-IVF, "
            "multi-cycle packages, grants (Baby Quest, Cade Foundation), "
            "military benefits (TriCare).\n\n"
            "Include a total cost estimator worksheet.  All figures in 2025-2026 USD.  "
            "Cite FertilityIQ, SART, and RESOLVE data."
        ),
    },
    "male-fertility-guide": {
        "title": "Male Fertility 101",
        "description": "Everything about sperm analysis, male factor, and what actually helps",
        "prompt": (
            "Create a comprehensive male fertility guide.  Male factor contributes to ~50% "
            "of infertility cases yet is under-discussed.\n\n"
            "**Semen Analysis Decoded** — Volume, concentration, total motile count, "
            "morphology (strict Kruger criteria), pH, liquefaction.  What each number means, "
            "WHO 6th edition reference values, common misinterpretations.\n\n"
            "**Beyond the Basics** — DNA fragmentation (SCSA, TUNEL, Comet), reactive oxygen "
            "species (ROS), anti-sperm antibodies.  When to test, what results mean.\n\n"
            "**Common Diagnoses** — Oligospermia, asthenospermia, teratospermia, "
            "azoospermia (obstructive vs non-obstructive), varicocele.  "
            "Evidence-based treatment for each.\n\n"
            "**What Actually Improves Sperm** — Evidence-graded interventions:\n"
            "- A-grade: varicocele repair, hormone therapy (for deficiency), "
            "lifestyle modification (smoking cessation, weight loss)\n"
            "- B-grade: antioxidant supplementation (CoQ10, vitamin C, zinc, selenium), "
            "reducing heat exposure, limiting alcohol\n"
            "- C-grade/unproven: specific diets, acupuncture, EMF avoidance\n\n"
            "**Timeline** — Spermatogenesis takes ~74 days.  When to expect improvement "
            "after interventions.  Retest timing.\n\n"
            "**When to See a Urologist** — Red flags, referral criteria.\n\n"
            "Cite ASRM Practice Committee opinions and Cochrane reviews."
        ),
    },
    "success-rate-guide": {
        "title": "How to Read Fertility Clinic Success Rates",
        "description": "Compare clinics using CDC data — what numbers actually matter",
        "prompt": (
            "Create a guide on interpreting fertility clinic success rates for patients.\n\n"
            "**Where to Find Data** — CDC ART Success Rates Report, SART.org, "
            "FertilityIQ clinic reports.  How to access each.\n\n"
            "**Key Metrics Explained** — Live birth rate per cycle started vs per transfer "
            "vs per intended egg retrieval.  Why 'per transfer' inflates numbers.  "
            "Cumulative live birth rate (the most meaningful metric).\n\n"
            "**Age Matters** — Breakdown by age group (<35, 35-37, 38-40, 41-42, 43+).  "
            "How to find YOUR age group's rates, not the clinic average.\n\n"
            "**Red Flags** — Clinics that cherry-pick patients, cancel 'hard' cycles, "
            "report only fresh transfer rates.  High cancellation rates.  "
            "Unusually high multiple rates (aggressive transfer policies).\n\n"
            "**Green Flags** — Single embryo transfer (SET) rates >80%, "
            "transparent reporting across all age groups, SART membership, "
            "low multiple pregnancy rates.\n\n"
            "**Apples to Apples** — How to normalize for patient mix (diagnosis, "
            "prior cycles, donor vs own eggs).  Why small clinics have volatile stats.\n\n"
            "**Questions to Ask Your Clinic** — 15 specific questions with what good "
            "answers look like.\n\n"
            "Cite CDC 2023 data reporting standards and ASRM guidelines."
        ),
    },
    "insurance-navigator": {
        "title": "Fertility Insurance Coverage Navigator",
        "description": "What your insurance covers, how to appeal, employer benefits",
        "prompt": (
            "Create an insurance coverage guide for fertility treatment in the US.\n\n"
            "**State Mandates** — Complete list of states with fertility insurance mandates "
            "(as of 2025-2026).  For each: what's covered (diagnosis only vs treatment), "
            "IVF included or excluded, lifetime caps, number of cycles, "
            "age limits, marriage requirements.\n\n"
            "**Employer Benefits** — Major fertility benefit platforms: "
            "Progyny (how it works, employer list), Carrot Fertility, Maven, "
            "WINFertility, Kindbody.  How to check if your employer offers these.\n\n"
            "**Insurance Terminology** — Deductible, coinsurance, out-of-pocket max, "
            "prior authorization, medical necessity, infertility diagnosis codes "
            "(ICD-10: N97.x, N46.x).  How each applies to fertility.\n\n"
            "**Appeal Process** — Step-by-step guide to appealing a denial: "
            "internal appeal, external review, state insurance commissioner complaint.  "
            "Template appeal letter.  What documentation to gather.\n\n"
            "**Alternative Funding** — FSA/HSA optimization, fertility grants "
            "(Baby Quest, Cade Foundation, Pay It Forward Fertility), "
            "clinical trials, shared-risk programs, fertility loans "
            "(Prosper, LendingClub, CapexMD).\n\n"
            "**Tax Implications** — Medical expense deduction (Schedule A), "
            "what qualifies, AGI threshold.\n\n"
            "Cite RESOLVE and state insurance commission data."
        ),
    },
    "preconception-guide": {
        "title": "30-Day Pre-Conception Wellness Plan",
        "description": "Evidence-backed lifestyle, diet, supplement, and timing guide",
        "prompt": (
            "Create a 30-day preconception plan for couples trying to conceive.\n\n"
            "**Week 1: Foundation** — Start prenatal vitamin (400-800mcg folate), "
            "baseline health check, dental visit (periodontal disease linked to preterm "
            "birth), medication review with doctor, stop smoking/alcohol/recreational drugs.  "
            "Male partner starts antioxidant supplement (CoQ10 200mg, zinc 30mg, "
            "vitamin C 500mg — evidence: B-grade).\n\n"
            "**Week 2: Nutrition** — Mediterranean diet pattern (A-grade evidence for "
            "fertility).  Specific foods: leafy greens (folate), fatty fish 2x/week "
            "(omega-3), full-fat dairy (linked to ovulatory fertility in NHS II study), "
            "avoid trans fats.  Limit caffeine to <200mg/day.  Hydration goals.\n\n"
            "**Week 3: Lifestyle Optimization** — Exercise (moderate, 150min/week — "
            "excessive exercise reduces fertility).  Sleep hygiene (7-9 hours, "
            "melatonin is a reproductive hormone).  Stress management "
            "(cortisol impacts GnRH pulsatility).  Environmental toxin reduction "
            "(BPA, phthalates, pesticides — switch to glass containers, "
            "clean produce list).\n\n"
            "**Week 4: Tracking & Timing** — Start BBT charting or OPK testing.  "
            "Understanding the fertile window (5 days before + day of ovulation).  "
            "Optimal intercourse frequency (every 1-2 days during fertile window).  "
            "Cervical mucus monitoring.  When to start 'trying' vs when to see a doctor "
            "(12 months if <35, 6 months if ≥35).\n\n"
            "**Both Partners** — Supplement evidence table with grades.  "
            "What NOT to take (high-dose vitamin A, certain herbs).\n\n"
            "**When to Skip Ahead** — Signs you should see an RE sooner "
            "(irregular cycles, known endometriosis, prior surgeries, >35).\n\n"
            "Cite ASRM, ACOG, and Cochrane reviews.  Grade every recommendation."
        ),
    },
}


class LeadMagnetGenerator:
    """Generate evidence-backed lead magnet guides using Claude."""

    def __init__(self, pipeline: "Pipeline", output_dir: Path) -> None:
        self.pipe = pipeline
        self._dir = output_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, magnet_name: str) -> Path:
        """Generate a lead magnet markdown file using Claude.

        Returns the path to the generated file.

        Raises:
            KeyError: If *magnet_name* is not in LEAD_MAGNETS.
        """
        if magnet_name not in LEAD_MAGNETS:
            raise KeyError(
                f"Unknown lead magnet '{magnet_name}'. "
                f"Available: {', '.join(LEAD_MAGNETS)}"
            )

        spec = LEAD_MAGNETS[magnet_name]
        output_path = self._dir / f"{magnet_name}.md"

        # Gather evidence context from the store
        evidence_context = self._gather_evidence()

        prompt = (
            f"# {spec['title']}\n\n"
            f"{spec['description']}\n\n"
            f"## Instructions\n\n{spec['prompt']}\n\n"
            f"## Available Evidence From Our Store\n\n{evidence_context}\n\n"
            "Write the complete guide in well-structured Markdown.  "
            "Use headers, bullet points, tables, and checkboxes where appropriate.  "
            "Every claim should reference its evidence grade (A/B/C).  "
            "End with a professional disclaimer about consulting a healthcare provider."
        )

        dispatcher = self.pipe.server.dispatcher
        body = ""

        if dispatcher:
            result = dispatcher.dispatch(
                agent_name="product-translator",
                skill_name="content-brief",
                prompt=prompt,
            )
            if result.status == "completed":
                body = result.output
            else:
                logger.warning(
                    "Claude dispatch failed for %s: %s", magnet_name, result.error
                )
                body = self._offline_stub(spec)
        else:
            body = self._offline_stub(spec)

        output_path.write_text(body, encoding="utf-8")
        logger.info("Generated lead magnet: %s -> %s", magnet_name, output_path)
        return output_path

    def list_available(self) -> list[dict[str, str]]:
        """Return metadata for all defined lead magnets."""
        result = []
        for name, spec in LEAD_MAGNETS.items():
            generated = (self._dir / f"{name}.md").exists()
            result.append({
                "name": name,
                "title": spec["title"],
                "description": spec["description"],
                "generated": str(generated),
            })
        return result

    def list_generated(self) -> list[str]:
        """Return names of lead magnets that have been generated."""
        return [
            p.stem
            for p in sorted(self._dir.glob("*.md"))
            if p.stem in LEAD_MAGNETS
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _gather_evidence(self, max_records: int = 10) -> str:
        """Pull top evidence records from the store for context."""
        records = self.pipe.evidence_store.all_records()[:max_records]
        if not records:
            return "(No evidence records in store — use general medical knowledge.)"
        lines = []
        for r in records:
            findings = "; ".join(r.key_findings) if r.key_findings else "N/A"
            lines.append(
                f"- [{r.source_feed}, {r.publication_date}] "
                f"{r.title} (grade {r.grade.value}): {findings}"
            )
        return "\n".join(lines)

    @staticmethod
    def _offline_stub(spec: dict[str, str]) -> str:
        """Generate a placeholder when Claude is unavailable."""
        return (
            f"# {spec['title']}\n\n"
            f"*{spec['description']}*\n\n"
            "---\n\n"
            "[This guide requires Claude API access to generate full content.  "
            "Run again with a valid ANTHROPIC_API_KEY.]\n\n"
            f"## Outline\n\n{spec['prompt']}\n"
        )
