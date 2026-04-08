"""Signal report — identifies people struggling with fertility and what outreach to run.

This is a FERTILITY demand-sensing report. The audience is men and women
who are trying to conceive, dealing with infertility, evaluating treatments,
or optimizing their reproductive health. NOT pregnancy/postpartum.

It answers:
1. Who is struggling with fertility right now?
2. What specific fertility problems are accelerating?
3. Where can we reach them (Reddit, forums, search, email)?
4. What evidence-backed content should we create and distribute?
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

# The fertility-focused journey stages — our core audience
FERTILITY_STAGES = {
    JourneyStage.PRECONCEPTION,
    JourneyStage.TRYING,
    JourneyStage.FERTILITY_TREATMENT,
}

# Audience labels focused on the fertility struggle
_STAGE_LABELS = {
    JourneyStage.PRECONCEPTION: "Optimizing fertility before trying",
    JourneyStage.TRYING: "Actively trying to conceive (TTC)",
    JourneyStage.FERTILITY_TREATMENT: "Undergoing fertility treatment (IVF/IUI/ART)",
}

# Intent → outreach type
_INTENT_CAMPAIGN = {
    TopicIntent.LEARN: "Educational outreach (blog, Reddit, social, email)",
    TopicIntent.DECIDE: "Decision-support tool (comparison, calculator, quiz)",
    TopicIntent.ACT: "Direct action (clinic referral, product rec, booking)",
    TopicIntent.MONITOR: "Tracking tool or check-in sequence",
    TopicIntent.COPE: "Community support + emotional outreach",
}

# Where to find this audience online
_STAGE_CHANNELS = {
    JourneyStage.PRECONCEPTION: {
        "subreddits": ["TryingForABaby", "WaitingForBaby", "TTC30", "TTC_PCOS"],
        "forums": ["WhatToExpect TTC board", "TheBump Getting Pregnant"],
        "search": ["Google: fertility + trying to conceive keywords"],
    },
    JourneyStage.TRYING: {
        "subreddits": ["TryingForABaby", "TTC30", "stilltrying", "TTC_PCOS", "maleinfertility"],
        "forums": ["WhatToExpect TTC board", "FertilityFriend community"],
        "search": ["Google: ovulation, OPK, fertility testing, TWW"],
    },
    JourneyStage.FERTILITY_TREATMENT: {
        "subreddits": ["infertility", "IVF", "InfertilityBabies", "maleinfertility"],
        "forums": ["FertilityIQ", "RESOLVE forums"],
        "search": ["Google: IVF cost, IVF success rates, fertility clinic reviews"],
    },
}


@dataclass
class AudienceSignal:
    """A demand signal — people struggling with a specific fertility problem."""
    topic_id: str
    display_name: str
    who: str
    struggle: str  # What they're dealing with
    journey_stage: str
    intent: str
    demand_score: float
    clinical_importance: float
    evidence_count: int
    outreach_type: str
    outreach_action: str
    where_to_find: dict[str, list[str]]  # Channels to reach them
    risk_tier: str
    flags: list[str] = field(default_factory=list)


@dataclass
class SignalReport:
    """Fertility demand intelligence report."""
    generated_at: datetime
    total_topics: int
    fertility_topics: int
    audience_signals: list[AudienceSignal]
    by_struggle: dict[str, list[AudienceSignal]]
    evidence_gaps: list[dict]
    summary: str
    campaign_brief: str


def _build_signal(
    topic: TopicNode, score: TopicOpportunityScore, evidence_count: int
) -> AudienceSignal:
    """Turn a scored fertility topic into an audience signal."""
    who = _STAGE_LABELS.get(topic.journey_stage, "People exploring fertility")

    # Build the struggle description — specific to fertility
    struggle_map = {
        "cycle-tracking": "Trying to predict ovulation and time intercourse",
        "irregular-periods": "Dealing with irregular cycles making it hard to predict fertility",
        "pcos-symptoms": "Struggling with PCOS affecting their ability to conceive",
        "ovulation": "Trying to understand and detect ovulation",
        "egg-quality": "Worried about egg quality, especially with age",
        "sperm-health": "Concerned about male factor fertility (sperm count, motility)",
        "amh-levels": "Got low AMH results and wondering what it means for fertility",
        "fertility-diet": "Looking for dietary changes to boost fertility",
        "fertility-supplements": "Researching supplements (CoQ10, folate, DHEA) for fertility",
        "opk-testing": "Using OPKs and trying to read results correctly",
        "bbt-charting": "Tracking basal body temperature to confirm ovulation",
        "timing-intercourse": "Figuring out the best timing for conception",
        "fertile-window": "Trying to identify their fertile window each cycle",
        "ivf": "Considering or going through IVF — overwhelmed by options and costs",
        "iui": "Evaluating IUI as a treatment option",
        "egg-freezing": "Considering egg freezing for future fertility",
        "clomid": "Prescribed Clomid and researching what to expect",
        "letrozole": "Starting letrozole and looking for others' experiences",
        "fertility-anxiety": "Dealing with the emotional toll of trying to conceive",
        "tww-coping": "In the two-week wait and struggling with anxiety",
        "pregnancy-loss": "Recovering from miscarriage and wondering about next steps",
        "miscarriage-risk": "Worried about miscarriage risk factors",
        "fertility-testing": "Getting fertility bloodwork and not sure what results mean",
        "semen-analysis": "Got semen analysis results and need to understand them",
        "hsg-test": "Preparing for or interpreting HSG test results",
        "genetic-screening": "Considering carrier screening before conceiving",
        "fertility-clinic-selection": "Choosing between fertility clinics",
    }
    struggle = struggle_map.get(
        topic.topic_id,
        f"Searching for help with {topic.display_name.lower()}"
    )

    # Outreach type
    outreach_type = _INTENT_CAMPAIGN.get(topic.intent, "Educational outreach")

    # Specific action
    if topic.monetization_class == MonetizationClass.REFERRAL:
        action = f"Connect them to fertility specialists for {topic.display_name.lower()}"
    elif topic.monetization_class == MonetizationClass.COMMERCE:
        action = f"Recommend evidence-backed products for {topic.display_name.lower()}"
    elif topic.monetization_class == MonetizationClass.TOOL:
        action = f"Build {topic.display_name.lower()} tool (calculator/tracker/checker)"
    elif evidence_count == 0:
        action = f"HOLD — need evidence before outreach on {topic.display_name.lower()}"
    else:
        action = f"Create + distribute content: {topic.display_name.lower()} guide"

    # Where to find them
    where = _STAGE_CHANNELS.get(topic.journey_stage, {
        "subreddits": ["TryingForABaby"],
        "search": ["Google fertility keywords"],
    })

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
        struggle=struggle,
        journey_stage=_STAGE_LABELS.get(topic.journey_stage, topic.journey_stage.value),
        intent=topic.intent.value,
        demand_score=score.demand_score,
        clinical_importance=score.clinical_importance,
        evidence_count=evidence_count,
        outreach_type=outreach_type,
        outreach_action=action,
        where_to_find=where,
        risk_tier=topic.risk_tier.value,
        flags=flags,
    )


def generate_report(pipe: Pipeline, top_n: int = 20) -> SignalReport:
    """Generate a fertility-focused demand signal report.

    ONLY includes preconception, trying, and fertility treatment stages.
    Pregnancy/postpartum/lactation topics are excluded.
    """
    all_scores = pipe.score(top_n=200)  # Score all, then filter
    all_evidence = pipe.evidence_store.all_records()

    # Evidence count per topic
    evidence_by_topic: dict[str, int] = {}
    for r in all_evidence:
        for tid in r.topics:
            evidence_by_topic[tid] = evidence_by_topic.get(tid, 0) + 1

    # Filter to fertility-focused stages only
    fertility_scores = []
    for s in all_scores:
        topic = pipe.graph.get_topic(s.topic_id)
        if topic and topic.journey_stage in FERTILITY_STAGES:
            fertility_scores.append((s, topic))

    # Build signals for top N fertility topics
    signals: list[AudienceSignal] = []
    for s, topic in fertility_scores[:top_n]:
        ec = evidence_by_topic.get(s.topic_id, 0)
        signals.append(_build_signal(topic, s, ec))

    # Group by struggle type (journey stage)
    by_struggle: dict[str, list[AudienceSignal]] = {}
    for sig in signals:
        by_struggle.setdefault(sig.journey_stage, []).append(sig)

    # Evidence gaps
    evidence_gaps = [
        {
            "topic_id": s.topic_id,
            "display_name": topic.display_name,
            "risk_tier": topic.risk_tier.value,
            "tos": s.composite_tos,
            "action": "Need evidence before outreach",
        }
        for s, topic in fertility_scores[:top_n]
        if evidence_by_topic.get(s.topic_id, 0) == 0 and topic.risk_tier != RiskTier.GREEN
    ]

    # Campaign brief
    actionable = [s for s in signals if "BLOCKED" not in s.flags and "NO_EVIDENCE" not in s.flags]
    ttc = [s for s in signals if "trying" in s.journey_stage.lower()]
    treatment = [s for s in signals if "treatment" in s.journey_stage.lower()]
    precon = [s for s in signals if "Optimizing" in s.journey_stage]

    brief_parts = [f"{len(signals)} fertility demand signals identified."]
    if ttc:
        brief_parts.append(f"TTC audience ({len(ttc)} signals): {', '.join(s.display_name for s in ttc[:3])}.")
    if treatment:
        brief_parts.append(f"Treatment audience ({len(treatment)} signals): {', '.join(s.display_name for s in treatment[:3])}.")
    if precon:
        brief_parts.append(f"Pre-TTC audience ({len(precon)} signals): {', '.join(s.display_name for s in precon[:3])}.")
    if evidence_gaps:
        brief_parts.append(f"{len(evidence_gaps)} topics need evidence before outreach.")

    summary = (
        f"{len(signals)} fertility signals. "
        f"{len(actionable)} ready for outreach. "
        f"{len(evidence_gaps)} need evidence."
    )

    return SignalReport(
        generated_at=datetime.utcnow(),
        total_topics=len(pipe.graph.all_topics()),
        fertility_topics=len(fertility_scores),
        audience_signals=signals,
        by_struggle=by_struggle,
        evidence_gaps=evidence_gaps,
        summary=summary,
        campaign_brief=" ".join(brief_parts),
    )


def format_report(report: SignalReport, as_json: bool = False) -> str:
    """Format for CLI display."""
    if as_json:
        return json.dumps({
            "generated_at": report.generated_at.isoformat(),
            "summary": report.summary,
            "campaign_brief": report.campaign_brief,
            "fertility_topics": report.fertility_topics,
            "signals": [
                {
                    "topic": s.topic_id,
                    "who": s.who,
                    "struggle": s.struggle,
                    "demand": s.demand_score,
                    "clinical": s.clinical_importance,
                    "evidence": s.evidence_count,
                    "action": s.outreach_action,
                    "where": s.where_to_find,
                    "flags": s.flags,
                }
                for s in report.audience_signals
            ],
            "evidence_gaps": report.evidence_gaps,
        }, indent=2)

    lines = []
    lines.append("=" * 90)
    lines.append("FERTILITY SENSE — WHO NEEDS HELP RIGHT NOW")
    lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Fertility topics: {report.fertility_topics} of {report.total_topics} total")
    lines.append("=" * 90)
    lines.append("")
    lines.append("CAMPAIGN BRIEF")
    lines.append(report.campaign_brief)
    lines.append("")

    lines.append("-" * 90)
    lines.append("PEOPLE STRUGGLING WITH FERTILITY — BY STAGE")
    lines.append("-" * 90)
    for stage, sigs in report.by_struggle.items():
        lines.append(f"\n  [{stage}]")
        for s in sigs:
            flag_str = f" [{', '.join(s.flags)}]" if s.flags else ""
            lines.append(f"    {s.display_name} (demand={s.demand_score:.0f}, clinical={s.clinical_importance:.0f}){flag_str}")
            lines.append(f"      Struggle: {s.struggle}")
            lines.append(f"      Action:   {s.outreach_action}")
            if s.where_to_find.get("subreddits"):
                lines.append(f"      Reddit:   {', '.join('r/' + sub for sub in s.where_to_find['subreddits'][:3])}")

    if report.evidence_gaps:
        lines.append("")
        lines.append("-" * 90)
        lines.append("EVIDENCE GAPS — Cannot reach out until we have clinical backing")
        lines.append("-" * 90)
        for gap in report.evidence_gaps:
            lines.append(f"  ! {gap['display_name']} ({gap['risk_tier']}) — {gap['action']}")

    lines.append("")
    lines.append("=" * 90)
    return "\n".join(lines)
