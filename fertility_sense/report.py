"""Signal report — identifies who is searching, what they're struggling with,
and what outreach/campaign actions to take.

This is a demand-sensing report for campaign planning. It answers:
1. What fertility problems are people actively searching about?
2. Where is demand accelerating (what's getting worse)?
3. What are the evidence-backed intervention points?
4. What outreach/campaign should we run to reach these people?
5. What gaps exist where people are searching but we can't help yet?
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime

from fertility_sense.models.scoring import TopicOpportunityScore
from fertility_sense.models.topic import (
    JourneyStage,
    MonetizationClass,
    RiskTier,
    TopicIntent,
    TopicNode,
)
from fertility_sense.pipeline import Pipeline


# Journey stage labels for human-readable output
_STAGE_LABELS = {
    JourneyStage.PRECONCEPTION: "Planning pregnancy",
    JourneyStage.TRYING: "Actively trying to conceive",
    JourneyStage.FERTILITY_TREATMENT: "In fertility treatment (IVF/IUI)",
    JourneyStage.PREGNANCY_T1: "Early pregnancy (T1)",
    JourneyStage.PREGNANCY_T2: "Mid pregnancy (T2)",
    JourneyStage.PREGNANCY_T3: "Late pregnancy (T3)",
    JourneyStage.LABOR_DELIVERY: "Labor & delivery",
    JourneyStage.POSTPARTUM: "Postpartum recovery",
    JourneyStage.LACTATION: "Breastfeeding",
}

# Intent → campaign type mapping
_INTENT_CAMPAIGN = {
    TopicIntent.LEARN: "Educational content campaign (blog, video, social)",
    TopicIntent.DECIDE: "Decision-support tool (comparison, quiz, calculator)",
    TopicIntent.ACT: "Direct action campaign (booking, product, referral)",
    TopicIntent.MONITOR: "Tracking tool or check-in sequence",
    TopicIntent.COPE: "Community + emotional support campaign",
}


@dataclass
class AudienceSignal:
    """A demand signal representing a group of people with a fertility problem."""
    topic_id: str
    display_name: str
    who: str  # Who is searching
    problem: str  # What they're struggling with
    journey_stage: str
    intent: str
    demand_score: float
    clinical_importance: float
    evidence_count: int
    campaign_type: str  # Recommended outreach type
    campaign_action: str  # Specific action to take
    risk_tier: str
    flags: list[str] = field(default_factory=list)


@dataclass
class SignalReport:
    """Actionable demand intelligence report for campaign planning."""
    generated_at: datetime
    total_topics: int
    scored_topics: int
    audience_signals: list[AudienceSignal]
    by_journey_stage: dict[str, list[AudienceSignal]]
    evidence_gaps: list[dict]
    safety_flags: list[dict]
    summary: str
    campaign_brief: str


def _build_audience_signal(
    topic: TopicNode, score: TopicOpportunityScore, evidence_count: int
) -> AudienceSignal:
    """Turn a scored topic into an audience signal with campaign recommendation."""
    who = _STAGE_LABELS.get(topic.journey_stage, "Fertility audience")
    problem = f"Searching about {topic.display_name.lower()}"

    # Enrich the "who" based on topic characteristics
    if topic.risk_tier == RiskTier.RED:
        who += " — need clinical-grade info"
    elif topic.intent == TopicIntent.COPE:
        who += " — seeking emotional support"
    elif topic.intent == TopicIntent.DECIDE:
        who += " — comparing options"

    # Campaign type from intent
    campaign_type = _INTENT_CAMPAIGN.get(topic.intent, "Content campaign")

    # Specific campaign action
    if topic.monetization_class == MonetizationClass.REFERRAL:
        campaign_action = f"Build referral flow: connect searchers to providers for {topic.display_name.lower()}"
    elif topic.monetization_class == MonetizationClass.COMMERCE:
        campaign_action = f"Product recommendation: curate evidence-backed {topic.display_name.lower()} options"
    elif topic.monetization_class == MonetizationClass.TOOL:
        campaign_action = f"Build interactive tool: {topic.display_name.lower()} calculator or checker"
    elif evidence_count == 0 and topic.risk_tier != RiskTier.GREEN:
        campaign_action = f"HOLD — ingest evidence before campaigning on {topic.display_name.lower()}"
    else:
        campaign_action = f"Create evidence-backed content on {topic.display_name.lower()} and distribute via SEO + social"

    flags = []
    if score.unsafe_to_serve:
        flags.append("BLOCKED")
    if score.escalate_to_human:
        flags.append("NEEDS_REVIEW")
    if evidence_count == 0:
        flags.append("NO_EVIDENCE")

    return AudienceSignal(
        topic_id=topic.topic_id,
        display_name=topic.display_name,
        who=who,
        problem=problem,
        journey_stage=_STAGE_LABELS.get(topic.journey_stage, topic.journey_stage.value),
        intent=topic.intent.value,
        demand_score=score.demand_score,
        clinical_importance=score.clinical_importance,
        evidence_count=evidence_count,
        campaign_type=campaign_type,
        campaign_action=campaign_action,
        risk_tier=topic.risk_tier.value,
        flags=flags,
    )


def generate_report(pipe: Pipeline, top_n: int = 20) -> SignalReport:
    """Generate an actionable signal report from the pipeline."""
    scores = pipe.score(top_n=top_n)
    all_topics = pipe.graph.all_topics()
    all_evidence = pipe.evidence_store.all_records()

    # Evidence count per topic
    evidence_by_topic: dict[str, int] = {}
    for r in all_evidence:
        for tid in r.topics:
            evidence_by_topic[tid] = evidence_by_topic.get(tid, 0) + 1

    # Build audience signals
    signals: list[AudienceSignal] = []
    for s in scores:
        topic = pipe.graph.get_topic(s.topic_id)
        if topic is None:
            continue
        ec = evidence_by_topic.get(s.topic_id, 0)
        signals.append(_build_audience_signal(topic, s, ec))

    # Group by journey stage
    by_stage: dict[str, list[AudienceSignal]] = {}
    for sig in signals:
        by_stage.setdefault(sig.journey_stage, []).append(sig)

    # Evidence gaps
    evidence_gaps = []
    for s in scores:
        topic = pipe.graph.get_topic(s.topic_id)
        if topic and topic.risk_tier != RiskTier.GREEN:
            ec = evidence_by_topic.get(s.topic_id, 0)
            if ec == 0:
                evidence_gaps.append({
                    "topic_id": s.topic_id,
                    "display_name": topic.display_name,
                    "risk_tier": topic.risk_tier.value,
                    "tos": s.composite_tos,
                    "action": "Ingest evidence before outreach",
                })

    # Safety flags
    safety_flags = [
        {
            "alert_id": a.alert_id,
            "title": a.title,
            "severity": a.severity.value,
            "affected_topics": a.affected_topics,
            "action": a.action_required,
        }
        for a in pipe._safety_alerts if not a.resolved
    ]

    # Campaign brief — synthesize the top signals into a brief
    actionable = [s for s in signals if "BLOCKED" not in s.flags and "NO_EVIDENCE" not in s.flags]
    content_targets = [s for s in actionable if s.campaign_type.startswith("Educational")]
    tool_targets = [s for s in actionable if "tool" in s.campaign_type.lower()]
    referral_targets = [s for s in actionable if "referral" in s.campaign_action.lower()]

    brief_parts = [f"Scored {len(signals)} topics across the fertility journey."]
    if actionable:
        brief_parts.append(f"{len(actionable)} are ready for outreach.")
    if content_targets:
        brief_parts.append(
            f"Content priority: {', '.join(s.display_name for s in content_targets[:3])}."
        )
    if tool_targets:
        brief_parts.append(
            f"Tool opportunity: {', '.join(s.display_name for s in tool_targets[:3])}."
        )
    if referral_targets:
        brief_parts.append(
            f"Referral pipeline: {', '.join(s.display_name for s in referral_targets[:3])}."
        )
    if evidence_gaps:
        brief_parts.append(f"{len(evidence_gaps)} topics need evidence before outreach.")

    # Summary
    summary = (
        f"{len(signals)} demand signals identified. "
        f"{len(actionable)} actionable now. "
        f"{len(evidence_gaps)} need evidence. "
        f"{len(safety_flags)} safety alerts active."
    )

    return SignalReport(
        generated_at=datetime.utcnow(),
        total_topics=len(all_topics),
        scored_topics=len(scores),
        audience_signals=signals,
        by_journey_stage=by_stage,
        evidence_gaps=evidence_gaps,
        safety_flags=safety_flags,
        summary=summary,
        campaign_brief=" ".join(brief_parts),
    )


def format_report(report: SignalReport, as_json: bool = False) -> str:
    """Format a SignalReport for CLI display."""
    if as_json:
        return json.dumps({
            "generated_at": report.generated_at.isoformat(),
            "summary": report.summary,
            "campaign_brief": report.campaign_brief,
            "audience_signals": [
                {
                    "topic": s.topic_id,
                    "who": s.who,
                    "problem": s.problem,
                    "demand": s.demand_score,
                    "clinical": s.clinical_importance,
                    "evidence": s.evidence_count,
                    "campaign": s.campaign_action,
                    "risk": s.risk_tier,
                    "flags": s.flags,
                }
                for s in report.audience_signals
            ],
            "by_journey_stage": {
                stage: [s.topic_id for s in sigs]
                for stage, sigs in report.by_journey_stage.items()
            },
            "evidence_gaps": report.evidence_gaps,
            "safety_flags": report.safety_flags,
        }, indent=2)

    lines = []
    lines.append("=" * 90)
    lines.append("FERTILITY-SENSE DEMAND SIGNAL REPORT")
    lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Coverage:  {report.scored_topics} of {report.total_topics} topics scored")
    lines.append("=" * 90)
    lines.append("")
    lines.append("CAMPAIGN BRIEF")
    lines.append(report.campaign_brief)
    lines.append("")

    # Audience signals by journey stage
    lines.append("-" * 90)
    lines.append("WHO IS SEARCHING & WHAT THEY NEED")
    lines.append("-" * 90)
    for stage, sigs in report.by_journey_stage.items():
        lines.append(f"\n  [{stage}]")
        for s in sigs:
            flag_str = f" [{', '.join(s.flags)}]" if s.flags else ""
            lines.append(f"    {s.display_name} (demand={s.demand_score:.0f}, clinical={s.clinical_importance:.0f}){flag_str}")
            lines.append(f"      -> {s.campaign_action}")

    # Evidence gaps
    if report.evidence_gaps:
        lines.append("")
        lines.append("-" * 90)
        lines.append("EVIDENCE GAPS — Cannot campaign until evidence is ingested")
        lines.append("-" * 90)
        for gap in report.evidence_gaps:
            lines.append(f"  ! {gap['display_name']} ({gap['risk_tier']}) — {gap['action']}")

    # Safety flags
    if report.safety_flags:
        lines.append("")
        lines.append("-" * 90)
        lines.append("SAFETY FLAGS")
        lines.append("-" * 90)
        for sf in report.safety_flags:
            lines.append(f"  ! [{sf['severity']}] {sf['title']}")

    lines.append("")
    lines.append("=" * 90)
    return "\n".join(lines)
