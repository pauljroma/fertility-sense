"""Lead magnet generator — B2B buyer guides and enablement content via Claude.

Generates downloadable content assets (ROI calculators, buyer guides, benchmarks)
that serve as lead magnets for B2B fertility benefit buyers (CHROs, brokers,
TPAs, unions).  Each guide is produced as a Markdown file in
``data/lead_magnets/{name}.md``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fertility_sense.pipeline import Pipeline

logger = logging.getLogger(__name__)


LEAD_MAGNETS: dict[str, dict[str, str]] = {
    "roi_calculator": {
        "title": "Fertility Benefit ROI Calculator: What It Actually Costs (and Saves)",
        "description": "Buyer guide showing fertility benefit cost components, hidden costs, and savings WIN delivers via network management",
        "prompt": (
            "Create a comprehensive fertility benefit ROI calculator and buyer guide for "
            "HR leaders and benefits decision-makers evaluating fertility benefit solutions. "
            "This guide is produced by WIN Fertility, the B2B fertility benefits management "
            "company that serves enterprise employers including Disney, Nvidia, and JPMorgan.\n\n"
            "**Cost Components Breakdown** — Walk through every cost that makes up a "
            "fertility benefit: per-member-per-month (PEPM) administrative fees, treatment "
            "cycle costs (IVF averaging $15-25K, IUI $2-5K, egg freezing $8-15K), fertility "
            "medications ($3-7K per cycle), genetic testing (PGT-A at $3-6K per batch), "
            "care navigation services, and claims administration. Show typical ranges by "
            "company size (100, 1,000, 10,000, 50,000+ employees).\n\n"
            "**Hidden Costs Most Employers Miss** — Detail the costs that don't show up in "
            "vendor proposals: open-network price variance (3x cost difference between "
            "providers for the same procedure), overutilization without clinical triage "
            "(15-20% of IVF candidates could succeed with less invasive treatment), "
            "pharmacy waste (brand vs generic, manufacturer rebates left on the table), "
            "employee productivity loss from poorly managed treatment journeys, and "
            "turnover costs when employees leave for companies with better benefits.\n\n"
            "**WIN Fertility Savings Model** — Explain how WIN's managed network approach "
            "delivers 20-40% savings: provider-level price negotiation across 900+ clinics, "
            "clinical care navigation that routes members to appropriate treatment, "
            "pharmacy management with direct manufacturer negotiations, and outcomes-based "
            "provider accountability. Include example calculations for a 5,000-employee "
            "company and a 50,000-employee company.\n\n"
            "**ROI Worksheet** — Provide a fill-in worksheet: current fertility spend, "
            "estimated utilization rate, current per-cycle cost, WIN benchmark per-cycle "
            "cost, projected annual savings, payback period. Include a retention ROI "
            "section: cost of replacing an employee ($50-200K) vs cost of fertility benefit "
            "($3-8 PEPM).\n\n"
            "**Industry Benchmarks** — Reference WIN's client base (Disney, Nvidia, JPM) "
            "and show typical costs by industry vertical: tech, finance, legal, "
            "manufacturing, healthcare. Format as a professional buyer guide with tables, "
            "charts described in text, and a clear call-to-action to request a custom "
            "analysis from WIN Fertility."
        ),
    },
    "broker_playbook": {
        "title": "Broker's Guide to Positioning WIN Fertility",
        "description": "Broker enablement doc: market opportunity, WIN differentiators, commission structure, talking points for CHRO meetings",
        "prompt": (
            "Create a comprehensive broker enablement guide for benefits brokers and "
            "consultants who want to add WIN Fertility to their solution portfolio. "
            "This guide is designed for producers at firms like Willis Towers Watson, "
            "AON, Marsh McLennan, Lockton, and regional brokerages.\n\n"
            "**Market Opportunity** — Fertility benefit utilization grew 31% year-over-year. "
            "68% of employees under 40 rank fertility in their top 5 desired benefits. "
            "The fertility benefits market is projected to reach $X billion by 2028. "
            "Employers are actively looking for solutions — this is a greenfield "
            "opportunity for brokers who can bring a differentiated offering.\n\n"
            "**WIN Fertility Differentiators** — Explain what makes WIN different from "
            "Progyny, Carrot, Maven, and Kindbody: (1) WIN is a benefits management "
            "company, not a provider — we manage the network, not compete with it; "
            "(2) provider-level cost negotiation across 900+ clinics; (3) clinical care "
            "navigation that reduces unnecessary treatment; (4) pharmacy management with "
            "manufacturer-direct pricing; (5) enterprise-grade reporting and compliance. "
            "WIN serves Disney, Nvidia, JPMorgan, and hundreds of mid-market employers.\n\n"
            "**Competitive Positioning** — Head-to-head comparison table: WIN vs Progyny "
            "(WIN manages costs, Progyny bundles them), WIN vs Carrot (WIN has deeper "
            "clinical navigation), WIN vs Maven (WIN focuses on fertility specifically, "
            "not broad women's health), WIN vs Kindbody (WIN is vendor-agnostic, "
            "Kindbody steers to owned clinics).\n\n"
            "**Commission Structure** — Outline the broker partnership model: ongoing "
            "commission on all employer contracts, no sunset clause, dedicated broker "
            "success team, co-branded materials, and custom proposals for each client.\n\n"
            "**CHRO Meeting Talking Points** — Provide 10 specific talking points brokers "
            "can use in benefits review meetings: cost trend data, competitive landscape, "
            "ROI framing, employee retention impact, implementation timeline (60 days), "
            "and proof points from WIN's enterprise client base. Include objection "
            "handling for common pushbacks: 'we already have Progyny,' 'fertility is "
            "niche,' 'our employees don't use it.'\n\n"
            "**RFP Support** — Explain how WIN supports brokers through the RFP process: "
            "custom proposals, finalist presentations, implementation planning, and "
            "ongoing account management. Format as a professional, print-ready guide."
        ),
    },
    "network_scorecard": {
        "title": "Fertility Provider Network Scorecard",
        "description": "Buyer-side rubric for evaluating fertility provider networks: size, specialty mix, outcomes data, cost transparency",
        "prompt": (
            "Create a fertility provider network evaluation scorecard for HR leaders "
            "and benefits decision-makers comparing fertility benefit vendors. This "
            "guide helps buyers ask the right questions and score vendors objectively. "
            "Produced by WIN Fertility, which manages a network of 900+ fertility "
            "providers serving enterprise employers like Disney, Nvidia, and JPMorgan.\n\n"
            "**Network Size & Geographic Coverage** — How to evaluate: total provider "
            "count, geographic distribution (coverage within 30/60/90 miles of employee "
            "populations), specialty mix (reproductive endocrinologists, urologists, "
            "mental health counselors, genetic counselors), and rural access. Scoring "
            "rubric: 1-5 scale with specific criteria for each score.\n\n"
            "**Provider Quality Metrics** — What to ask for: clinic-level live birth "
            "rates (not network averages), SART membership rates, single embryo transfer "
            "rates, cancellation rates, complication rates. How to spot vendors who "
            "cherry-pick data or report inflated metrics. Scoring rubric.\n\n"
            "**Cost Transparency** — Critical evaluation criteria: does the vendor "
            "negotiate provider-level pricing or just pass through claims? Can they "
            "show per-cycle cost by provider? Do they share pharmacy pricing? Is there "
            "a cost guarantee or performance-based model? Most vendors cannot answer "
            "these questions — that's a red flag. Scoring rubric.\n\n"
            "**Care Navigation & Clinical Oversight** — Evaluate: who does the clinical "
            "triage (nurses, social workers, algorithms)? Is there a medical director? "
            "How are treatment plans reviewed? What happens when a member is on an "
            "inappropriate treatment path? WIN's model: registered nurse care navigators "
            "with physician oversight. Scoring rubric.\n\n"
            "**Member Experience** — Evaluate: member portal, care navigation "
            "responsiveness, mental health support, pharmacy coordination, multilingual "
            "support. Include specific questions to ask vendors and what good answers "
            "look like.\n\n"
            "**Integration & Reporting** — Evaluate: eligibility integration, claims "
            "data flow, reporting capabilities, ERISA compliance support. Scoring rubric.\n\n"
            "**Summary Scorecard Template** — Provide a printable scorecard with all "
            "categories, weights, and a total score calculation. Include a 'green/yellow/"
            "red' interpretation guide. Note that WIN Fertility welcomes this evaluation "
            "process — our network is designed to score well on every dimension."
        ),
    },
    "cost_benchmark": {
        "title": "Fertility Benefit Cost Benchmarks: Industry & Company Size",
        "description": "Benchmark report: typical costs by industry and company size, with WIN's cost positioning",
        "prompt": (
            "Create a fertility benefit cost benchmark report for employers evaluating "
            "fertility benefit options. This report provides data-backed cost benchmarks "
            "by industry vertical and company size, helping HR leaders understand where "
            "they stand and what they should expect to pay. Produced by WIN Fertility, "
            "based on data from our enterprise client base including Disney, Nvidia, "
            "and JPMorgan.\n\n"
            "**National Averages** — Current average costs for fertility benefits: "
            "PEPM administrative fees ($2-8 depending on plan design), average IVF "
            "cycle cost ($15-25K open network, $9-14K managed network), average "
            "medication cost per cycle ($3-7K), average total cost per fertility "
            "treatment episode ($20-40K open network). Utilization rates: typically "
            "0.5-2% of covered lives per year, varying by demographics.\n\n"
            "**By Industry Vertical** — Detailed cost benchmarks for:\n"
            "- Tech (high utilization, younger workforce, egg freezing demand)\n"
            "- Finance (moderate utilization, high expectations for coverage quality)\n"
            "- Legal (small firms, high per-capita income, retention-focused)\n"
            "- Manufacturing (lower utilization, geographically dispersed, cost-sensitive)\n"
            "- Healthcare (moderate utilization, clinically sophisticated buyers)\n"
            "For each: typical utilization rate, average per-cycle cost, typical plan "
            "design, and what top employers in the sector offer.\n\n"
            "**By Company Size** — Cost benchmarks for:\n"
            "- 100-500 employees: PEPM, expected utilization, total annual cost\n"
            "- 500-2,000 employees: same metrics\n"
            "- 2,000-10,000 employees: same metrics\n"
            "- 10,000-50,000 employees: same metrics\n"
            "- 50,000+ employees: same metrics\n\n"
            "**WIN Fertility Cost Positioning** — Show how WIN's managed approach "
            "compares to open-network and competitor benchmarks. WIN typically delivers "
            "20-40% savings on per-cycle costs through provider negotiation, clinical "
            "triage, and pharmacy management. Include specific savings examples.\n\n"
            "**Cost Trend Projections** — Where costs are heading: fertility utilization "
            "growing 25-35% annually, medication costs increasing, but managed solutions "
            "are bending the curve. What employers should budget for 2026-2028.\n\n"
            "Format as a professional benchmark report with tables and clear data "
            "presentation. Include a call-to-action to request a custom benchmark "
            "analysis from WIN Fertility."
        ),
    },
    "compliance_guide": {
        "title": "Fertility Mandates & ERISA Compliance for Employers",
        "description": "Compliance brief: state fertility mandates, ERISA implications, what employers must offer",
        "prompt": (
            "Create a comprehensive compliance guide on fertility benefit mandates and "
            "ERISA implications for employers. This guide helps HR leaders, benefits "
            "attorneys, and compliance teams understand their legal obligations around "
            "fertility benefits. Produced by WIN Fertility, which manages fertility "
            "benefits compliance for enterprise employers including Disney, Nvidia, "
            "and JPMorgan.\n\n"
            "**State Fertility Mandates Overview** — As of 2026, 21+ states have some "
            "form of fertility insurance mandate. For each state with a mandate, detail: "
            "what's required (diagnosis coverage only vs treatment coverage), whether IVF "
            "is included, lifetime dollar caps, cycle limits, age restrictions, "
            "marriage requirements, and which employer types are subject to the mandate "
            "(fully insured only vs all employers). Organize as a state-by-state table.\n\n"
            "**ERISA Implications** — Explain the ERISA preemption: self-funded employers "
            "are generally exempt from state mandates but face federal requirements. "
            "Cover: ERISA preemption scope, Mental Health Parity implications for "
            "fertility (emerging legal theory), ACA essential health benefits interaction, "
            "and non-discrimination requirements under Section 1557. Explain how "
            "self-funded plans can voluntarily adopt fertility coverage and the "
            "advantages of doing so.\n\n"
            "**Compliance Best Practices** — What employers should do regardless of "
            "mandate status: consistent plan language, non-discriminatory benefit design "
            "(covering same-sex couples, single parents, LGBTQ+ individuals), "
            "documentation requirements, SPD language, and claims appeal procedures. "
            "Cover the EEOC's position on fertility benefits and pregnancy "
            "discrimination.\n\n"
            "**Common Compliance Pitfalls** — Mistakes employers make: inconsistent "
            "coverage across subsidiaries/states, discriminatory eligibility criteria, "
            "inadequate network access, failure to update plan documents, and "
            "non-compliant claims denials.\n\n"
            "**WIN Fertility Compliance Support** — Explain how WIN helps employers "
            "navigate compliance: plan document templates, state mandate tracking, "
            "non-discrimination review, and ongoing regulatory monitoring. WIN's legal "
            "and compliance team stays current so employers don't have to.\n\n"
            "Include a compliance checklist and a state mandate quick-reference table. "
            "Note: this is educational content, not legal advice. Recommend consultation "
            "with benefits counsel."
        ),
    },
    "union_value_prop": {
        "title": "Fertility Benefits for Union Members: The Business Case",
        "description": "Union-focused content: member retention impact, negotiation leverage, network access for geographically dispersed members",
        "prompt": (
            "Create a comprehensive business case for adding fertility benefits to "
            "union health trust plans. This guide targets union benefits directors, "
            "trust administrators, and labor negotiators. Produced by WIN Fertility, "
            "which manages fertility benefits for enterprise employers including "
            "Disney, Nvidia, and JPMorgan, and partners with labor organizations "
            "across industries.\n\n"
            "**Member Demand Data** — 68% of workers under 40 rank fertility benefits "
            "in their top 5 most desired benefits. Union members are increasingly vocal "
            "about fertility coverage during contract negotiations. Show survey data, "
            "demographic trends (delayed family formation), and how fertility benefits "
            "compare to other high-demand benefits in member satisfaction surveys.\n\n"
            "**Member Retention Impact** — Fertility benefits drive retention: "
            "employees with access to fertility benefits are X% more likely to stay. "
            "For unions, member retention means dues revenue, bargaining power, and "
            "organizational strength. Calculate the cost of losing a member vs the cost "
            "of providing fertility coverage. Include ROI framing specific to unions.\n\n"
            "**Negotiation Leverage** — How to position fertility benefits at the "
            "bargaining table: it's a high-value, moderate-cost benefit that employers "
            "increasingly expect to offer. Unions that negotiate fertility coverage "
            "demonstrate modern, comprehensive advocacy for members. Include talking "
            "points for contract negotiations and how to frame the ask relative to "
            "other benefit improvements.\n\n"
            "**Geographic Coverage for Dispersed Membership** — Union members often "
            "work across multiple states and regions. WIN Fertility's network of 900+ "
            "providers spans all 50 states, ensuring members get local access to "
            "quality fertility care regardless of where they live or work. Compare "
            "this to vendor-owned clinic models that concentrate in major metros.\n\n"
            "**Cost Management for Trust Plans** — Union health trusts are fiduciaries "
            "for member contributions. Show how WIN's managed approach keeps costs "
            "predictable: negotiated provider rates (25-35% below open network), "
            "clinical triage to prevent overutilization, pharmacy management, and "
            "fixed administrative fees. Include cost modeling for a 10,000-member and "
            "50,000-member trust.\n\n"
            "**Mental Health and Support Services** — Fertility treatment is "
            "emotionally demanding. WIN provides access to fertility-specialized mental "
            "health counselors as part of the benefit. This matters for union members "
            "who may not have easy access to specialized support.\n\n"
            "**Implementation** — How adding WIN Fertility works for a union trust: "
            "60-day implementation, no disruption to existing benefits, and ongoing "
            "reporting to trust administrators. Include a timeline and checklist.\n\n"
            "Format as a professional business case document with executive summary, "
            "data tables, and a clear recommendation. Include a call-to-action to "
            "schedule a trust administrator briefing with WIN Fertility."
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
