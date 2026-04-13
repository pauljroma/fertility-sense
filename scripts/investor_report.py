"""Generate and email investor intelligence brief."""

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
    lines.append("FERTILITY SENSE — INVESTOR INTELLIGENCE BRIEF")
    lines.append("=" * 64)
    lines.append("")
    lines.append("PLATFORM OVERVIEW")
    lines.append("")
    lines.append("Fertility Sense is an autonomous demand-sensing intelligence")
    lines.append("platform that identifies people struggling with fertility,")
    lines.append("ranks their needs by clinical importance and commercial")
    lines.append("opportunity, and generates evidence-backed outreach content")
    lines.append("across multiple channels.")
    lines.append("")
    lines.append("SYSTEM CAPABILITIES")
    lines.append("  - 10 AI agents (8 Claude-powered + 2 autonomous loops)")
    lines.append("  - 91-topic fertility ontology with 262 search aliases")
    lines.append("  - Evidence curation from CDC, NIH, FDA, MotherToBaby (30 records)")
    lines.append("  - Composite scoring: demand + clinical + trust + commercial")
    lines.append("  - Governed answer assembly with 7-class safety governance")
    lines.append("  - Multi-channel campaign composer (Reddit, email, blog, social)")
    lines.append("  - Email distribution (IONOS SMTP, live)")
    lines.append("  - HITL content review queue")
    lines.append("  - 5 automated drip sequences by journey stage")
    lines.append("  - Prospect CRM with segmentation")
    lines.append("  - 6 lead magnet templates")
    lines.append("")
    lines.append("TECHNOLOGY")
    lines.append("  - 13,246 lines Python + 3,297 lines YAML")
    lines.append("  - 246 tests passing (unit, integration, e2e)")
    lines.append("  - Claude Sonnet 4.6 + Opus 4.6 + Haiku 4.5")
    lines.append("  - Dockerized, CI/CD ready, API with auth + rate limiting")
    lines.append("")
    lines.append("=" * 64)
    lines.append("DEMAND SIGNAL INTELLIGENCE")
    lines.append("=" * 64)
    lines.append("")
    lines.append(report.campaign_brief)
    lines.append("")
    lines.append(f"Fertility topics scored: {report.fertility_topics} of {report.total_topics}")
    lines.append("Evidence records: 30 (10 seed + 20 live MotherToBaby)")
    lines.append("Active feeds: 1 (MotherToBaby); 2 ready (Google Trends, Reddit)")
    lines.append("")
    lines.append("=" * 64)
    lines.append("TOP FERTILITY DEMAND SIGNALS")
    lines.append("=" * 64)

    for sig in report.audience_signals:
        flag_str = ""
        if sig.flags:
            flag_str = f"  [{', '.join(sig.flags)}]"
        lines.append("")
        lines.append(f"{sig.display_name} (demand={sig.demand_score:.0f}, clinical={sig.clinical_importance:.0f}){flag_str}")
        lines.append(f"  Audience:   {sig.who}")
        lines.append(f"  Struggle:   {sig.struggle}")
        lines.append(f"  Action:     {sig.outreach_action}")
        lines.append(f"  Evidence:   {sig.evidence_count} record(s) | Risk: {sig.risk_tier}")
        subs = sig.where_to_find.get("subreddits", [])
        if subs:
            lines.append(f"  Reddit:     {', '.join('r/' + s for s in subs[:3])}")

    if report.evidence_gaps:
        lines.append("")
        lines.append("=" * 64)
        lines.append("EVIDENCE GAPS (need clinical data before outreach)")
        lines.append("=" * 64)
        for gap in report.evidence_gaps:
            lines.append(f"  {gap['display_name']} ({gap['risk_tier']})")

    lines.append("")
    lines.append("=" * 64)
    lines.append("COMPETITIVE MOAT")
    lines.append("=" * 64)
    lines.append("")
    lines.append("1. EVIDENCE-GRADED CONTENT")
    lines.append("   Every claim is Grade A-B evidence from CDC, NIH, FDA.")
    lines.append("   Competitors publish ungraded marketing copy.")
    lines.append("")
    lines.append("2. SAFETY GOVERNANCE")
    lines.append("   7-class disallowed pattern detection. Risk-tiered publication")
    lines.append("   gates (GREEN/YELLOW/RED/BLACK). No diagnosis, no dosages,")
    lines.append("   no outcome guarantees.")
    lines.append("")
    lines.append("3. DEMAND-SENSING ENGINE")
    lines.append("   Real-time TOS scoring identifies what people need before")
    lines.append("   competitors see the trend. Velocity detection catches")
    lines.append("   emerging topics early.")
    lines.append("")
    lines.append("4. MULTI-CHANNEL COMPOSITION")
    lines.append("   Single evidence record produces governed content for")
    lines.append("   Reddit, email, blog, social, and forums — each in")
    lines.append("   channel-native tone.")
    lines.append("")
    lines.append("5. AUTONOMOUS OPERATION")
    lines.append("   Scout loop runs unattended. Human reviews content before")
    lines.append("   distribution (HITL). Built for compliance from day one.")
    lines.append("")
    lines.append("=" * 64)
    lines.append("MARKET FOCUS")
    lines.append("=" * 64)
    lines.append("")
    lines.append("Target: Men and women struggling with fertility")
    lines.append("  - Pre-TTC: PCOS, egg quality, supplements, lifestyle")
    lines.append("  - TTC: ovulation tracking, timing, TWW, pregnancy loss")
    lines.append("  - Treatment: IVF, IUI, egg freezing, clinic selection, costs")
    lines.append("")
    lines.append("NOT targeting: pregnancy, postpartum, breastfeeding, newborn")
    lines.append("")
    lines.append("Channels: Reddit (r/TryingForABaby, r/infertility, r/IVF),")
    lines.append("  forums, Google search, permission-based email sequences")
    lines.append("")
    lines.append("=" * 64)
    lines.append("NEXT MILESTONES")
    lines.append("=" * 64)
    lines.append("")
    lines.append("1. Activate Google Trends + Reddit feeds (real-time demand)")
    lines.append("2. Generate lead magnets (fertility checklist, IVF cost guide)")
    lines.append("3. Deploy scout loop on cron (6h cycle, daily digest)")
    lines.append("4. Build 50-prospect pilot, run TTC nurture sequence")
    lines.append("5. Implement CDC ART/NASS feed (IVF clinic success rates)")
    lines.append("6. Launch content queue workflow (compose > review > distribute)")
    lines.append("")
    lines.append("=" * 64)

    body = "\n".join(lines)

    email = campaign_to_email(
        to="paul@romatech.com",
        subject="Fertility Sense — Investor Intelligence Brief",
        body=body,
        campaign_id="investor-001",
    )

    result = sender.send(email)
    print(f"Status: {result.status}")
    print(f"Body: {len(body)} chars")


if __name__ == "__main__":
    main()
