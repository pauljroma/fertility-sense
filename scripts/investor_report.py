"""Generate and email WIN Fertility investor / pipeline intelligence brief."""

from fertility_sense.config import FertilitySenseConfig
from fertility_sense.pipeline import Pipeline
from fertility_sense.report import generate_report
from fertility_sense.outreach.email_sender import EmailSender, campaign_to_email


def main():
    config = FertilitySenseConfig()
    pipe = Pipeline(config)
    sender = EmailSender(config)

    report = generate_report(pipe, top_n=15)

    lines = []
    lines.append("WIN FERTILITY — PIPELINE & GROWTH INTELLIGENCE")
    lines.append("=" * 64)
    lines.append("")

    # --- THE COMPANY ---
    lines.append("THE COMPANY")
    lines.append("")
    lines.append("WIN Fertility is a tech-enabled fertility benefit management")
    lines.append("platform. We sell to CHROs at large enterprises (Disney, Nvidia,")
    lines.append("JPM), small companies, labor unions, TPAs, and via brokers")
    lines.append("(Willis, AON, Marsh). We manage a performance + cost driven")
    lines.append("network of fertility doctors, mental health counselors, and drug")
    lines.append("companies — negotiating discounts and delivering best treatment")
    lines.append("at lowest cost.")
    lines.append("")

    # --- GROWTH ENGINE OVERVIEW ---
    lines.append("=" * 64)
    lines.append("GROWTH ENGINE OVERVIEW")
    lines.append("=" * 64)
    lines.append("")
    lines.append("  - 10 AI agents continuously monitoring B2B demand signals")
    lines.append("  - Multi-channel outreach: LinkedIn, sales email, case studies, broker briefs")
    lines.append("  - 6 buyer-segmented email sequences (CHRO, broker, SMB, union, TPA, re-engagement)")
    lines.append("  - 6 lead magnets calibrated to each buyer type")
    lines.append("  - Evidence-graded clinical content (CDC, NIH, FDA sources)")
    lines.append("  - HITL content review queue")
    lines.append("  - Email delivery via IONOS SMTP")
    lines.append("  - 246 tests, ~13K LOC, production-ready")
    lines.append("")

    # --- BUYER PIPELINE ---
    lines.append("=" * 64)
    lines.append("BUYER PIPELINE (live)")
    lines.append("=" * 64)
    lines.append("")

    # Pull live signal counts from report
    actionable = [s for s in report.audience_signals if "BLOCKED" not in s.flags and "NO_EVIDENCE" not in s.flags]
    lines.append(f"  Total demand signals tracked: {len(report.audience_signals)}")
    lines.append(f"  Actionable (ready for outreach): {len(actionable)}")
    lines.append("")
    lines.append("  - CHRO outbound: [N companies, M evaluating — fill from CRM]")
    lines.append("  - Broker partnerships: [N producers engaged — fill from CRM]")
    lines.append("  - SMB pipeline: [N small companies — fill from CRM]")
    lines.append("  - Union conversations: [N — fill from CRM]")
    lines.append("  - TPA integrations: [N — fill from CRM]")
    lines.append("")

    # --- DEMAND INTELLIGENCE ---
    lines.append("=" * 64)
    lines.append("DEMAND INTELLIGENCE (this period)")
    lines.append("=" * 64)
    lines.append("")
    lines.append(report.campaign_brief)
    lines.append("")
    lines.append(f"  Fertility topics scored: {report.fertility_topics} of {report.total_topics}")
    lines.append("")

    # Top signals as demand intelligence
    lines.append("  Top fertility topics driving employee inquiries:")
    for i, sig in enumerate(report.audience_signals[:10], 1):
        flag_str = ""
        if sig.flags:
            flag_str = f"  [{', '.join(sig.flags)}]"
        lines.append(f"    {i:2d}. {sig.display_name} (demand={sig.demand_score:.0f}, clinical={sig.clinical_importance:.0f}){flag_str}")
    lines.append("")
    lines.append("  Buyer pain mapping:")
    lines.append("    - Cost: Employees overwhelmed by IVF/treatment pricing")
    lines.append("    - Retention: Top talent choosing employers with fertility benefits")
    lines.append("    - Network gaps: Employees struggling to find quality providers")
    lines.append("")

    # --- CHANNEL ECONOMICS ---
    lines.append("=" * 64)
    lines.append("CHANNEL ECONOMICS")
    lines.append("=" * 64)
    lines.append("")
    lines.append("  - Enterprise direct: $100K+ ARR per win, 6-9 month sales cycle")
    lines.append("  - Broker channel: 15-20% commission, 3-month activation")
    lines.append("  - SMB inbound: $20K-50K ARR, 2-month cycle")
    lines.append("  - Union RFPs: $50K-250K ARR per multi-year deal")
    lines.append("  - TPA integration: 12-18 month enterprise sales")
    lines.append("")

    # --- NETWORK ---
    lines.append("=" * 64)
    lines.append("NETWORK")
    lines.append("=" * 64)
    lines.append("")
    lines.append("  - [network size] fertility doctors (vetted, performance-tracked)")
    lines.append("  - [network size] mental health counselors (fertility-trained)")
    lines.append("  - [network size] drug company partnerships (negotiated discount tier)")
    lines.append("")

    # --- COMPETITIVE POSITION ---
    lines.append("=" * 64)
    lines.append("COMPETITIVE POSITION")
    lines.append("=" * 64)
    lines.append("")
    lines.append("  vs. Progyny: Smaller network but stronger cost negotiations")
    lines.append("  vs. Carrot/Maven: Deeper clinical management vs. concierge nav")
    lines.append("  vs. Kindbody: Flexible network model vs. owned clinics")
    lines.append("")

    # --- EVIDENCE GAPS ---
    if report.evidence_gaps:
        lines.append("=" * 64)
        lines.append("EVIDENCE GAPS (need clinical data before outreach)")
        lines.append("=" * 64)
        lines.append("")
        for gap in report.evidence_gaps:
            lines.append(f"  {gap['display_name']} ({gap['risk_tier']})")
        lines.append("")

    # --- NEXT MILESTONES ---
    lines.append("=" * 64)
    lines.append("NEXT MILESTONES")
    lines.append("=" * 64)
    lines.append("")
    lines.append("  1. Activate Reddit + Google Trends signals -> qualified inbound leads")
    lines.append("  2. Launch broker enablement campaign (Willis, AON, Marsh)")
    lines.append("  3. CHRO outbound to top 50 target accounts (Fortune 500)")
    lines.append("  4. Publish 3 case studies (Disney, Nvidia, JPM — anonymized)")
    lines.append("  5. RFP response engine for union/TPA opportunities")
    lines.append("")
    lines.append("=" * 64)

    body = "\n".join(lines)

    email = campaign_to_email(
        to="paul@romatech.com",
        subject="WIN Fertility — Pipeline & Growth Intelligence Brief",
        body=body,
        campaign_id="win-investor-001",
    )

    result = sender.send(email)
    print(f"Status: {result.status}")
    print(f"Body: {len(body)} chars")


if __name__ == "__main__":
    main()
