"""Signal report — identifies pipeline opportunities for WIN Fertility B2B sales.

This is a B2B pipeline intelligence report. The audience is WIN Fertility's
sales team targeting CHROs, brokers, SMBs, unions, TPAs, and partners.

It answers:
1. Which buyer types have the strongest demand signals right now?
2. What specific fertility benefit pain points are accelerating?
3. Where can we reach each buyer type (LinkedIn, conferences, broker channels)?
4. What sales content should we create and distribute?
5. What data gaps exist where we need more market intelligence?

Backward-compatible: AudienceSignal, generate_report(), format_report() still work.
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

# Intent -> outreach type
_INTENT_CAMPAIGN = {
    TopicIntent.LEARN: "Educational outreach (blog, social, email)",
    TopicIntent.DECIDE: "Decision-support tool (comparison, calculator, quiz)",
    TopicIntent.ACT: "Direct action (clinic referral, product rec, booking)",
    TopicIntent.MONITOR: "Tracking tool or check-in sequence",
    TopicIntent.COPE: "Community support + emotional outreach",
}

# Where to find this audience online (legacy consumer channels)
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


# ======================================================================
# B2B: Buyer pain points by topic
# ======================================================================

_BUYER_PAIN_FOR_TOPIC: dict[str, str] = {
    "ivf": "Employees requesting IVF coverage drive 30%+ of fertility benefit spend",
    "pcos-symptoms": "PCOS affects 1 in 10 female employees — retention risk",
    "egg-quality": "Egg freezing demand from women 30+ — retention play",
    "egg-freezing": "Egg freezing demand from women 30+ — retention play",
    "fertility-clinic-selection": "Network quality complaints drive employee dissatisfaction",
    "pregnancy-loss": "Mental health support gap — emerging RFP requirement",
    "iui": "IUI coverage requests increasing — lower-cost alternative to IVF",
    "fertility-supplements": "Supplement coverage questions signal employees exploring fertility options",
    "sperm-health": "Male factor infertility underserved — differentiation opportunity",
    "fertility-anxiety": "Mental health support is the #1 emerging RFP requirement for fertility benefits",
    "fertility-testing": "Diagnostic coverage gaps create employee friction and support ticket volume",
    "clomid": "Rx coverage for fertility medications — drug cost management opportunity",
    "letrozole": "Rx coverage for fertility medications — drug cost management opportunity",
    "fertility-diet": "Wellness and nutrition support signals employee engagement with fertility benefits",
    "cycle-tracking": "Cycle tracking benefit demand signals pre-treatment employee engagement",
    "irregular-periods": "Diagnostic pathway coverage gaps — early intervention reduces downstream IVF costs",
    "ovulation": "Ovulation support needs signal employees in early fertility journey — low-cost intervention window",
    "amh-levels": "Diagnostic testing demand — early assessment reduces downstream treatment costs",
    "opk-testing": "OPK and monitoring coverage requests signal growing fertility awareness in workforce",
    "bbt-charting": "Tracking tool demand signals employee engagement with fertility wellness programs",
    "timing-intercourse": "Education and support needs at pre-treatment stage — low-cost engagement",
    "fertile-window": "Fertility awareness demand signals workforce planning benefit gaps",
    "tww-coping": "Two-week wait anxiety drives mental health support utilization",
    "miscarriage-risk": "Pregnancy loss support is an emerging must-have in fertility benefit RFPs",
    "semen-analysis": "Male factor diagnostic coverage — underserved but growing RFP requirement",
    "hsg-test": "Diagnostic procedure coverage — standard fertility workup component",
    "genetic-screening": "Carrier screening coverage demand increasing — PGT-A is a cost driver",
}


def _buyer_pain_for_topic(topic_id: str) -> str:
    """Return the B2B buyer pain point associated with a topic."""
    return _BUYER_PAIN_FOR_TOPIC.get(
        topic_id,
        f"Fertility benefit demand signal: {topic_id.replace('-', ' ')}"
    )


# Where to find each buyer type
_BUYER_CHANNELS: dict[str, dict[str, list[str]]] = {
    "chro": {
        "linkedin": ["CHRO communities", "Benefits leadership groups"],
        "conferences": ["SHRM Annual", "HLTH", "WorldatWork"],
        "reports": ["AON Health Survey", "Mercer Benefits Survey"],
        "direct": ["Direct outreach via LinkedIn Sales Navigator"],
    },
    "broker": {
        "channels": ["Willis internal portal", "AON Marketplace", "Marsh network"],
        "conferences": ["RIMS", "BenefitsPRO Broker Expo", "NAHU"],
        "publications": ["BenefitsPRO", "Employee Benefit Adviser"],
    },
    "smb": {
        "linkedin": ["HR professionals groups", "Small business owner networks"],
        "publications": ["ALM Intelligence", "SHRM for small business"],
        "associations": ["NAPEO", "local SHRM chapters"],
    },
    "union": {
        "channels": ["Union benefits councils", "AFL-CIO benefits network"],
        "conferences": ["IFEBP Annual Conference"],
        "direct": ["Union benefits director outreach"],
    },
    "tpa": {
        "channels": ["TPA partner directories", "SIIA membership"],
        "conferences": ["SIIA National Conference"],
        "direct": ["Integration partnership outreach"],
    },
    "partner": {
        "linkedin": ["Private equity healthcare groups"],
        "conferences": ["JPM Healthcare Conference", "HLTH"],
        "direct": ["Strategic partnership development"],
    },
}


def _where_to_find_buyer(buyer_type: str = "") -> dict[str, list[str]]:
    """Return channels to reach a specific buyer type."""
    return _BUYER_CHANNELS.get(buyer_type, {
        "linkedin": ["Benefits leadership groups"],
        "conferences": ["SHRM", "HLTH"],
    })


# ======================================================================
# Backward-compatible AudienceSignal
# ======================================================================


@dataclass
class AudienceSignal:
    """A demand signal — people struggling with a specific fertility problem.

    Kept for backward compatibility. New code should also populate
    BuyerSignal fields via generate_pipeline_intelligence().
    """
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


# ======================================================================
# B2B: BuyerSignal
# ======================================================================


@dataclass
class BuyerSignal:
    """A B2B buyer signal — a company/buyer with a fertility benefit need."""
    topic_id: str
    display_name: str
    buyer_type: str  # chro, broker, smb, union, tpa, partner
    buyer_context: str  # who they are
    pain_point: str  # what they need solved
    deal_stage: str  # cold, warm, evaluating, negotiating
    sales_motion: str  # outbound, broker_enablement, rfp_response, etc.
    pipeline_value_estimate: str  # e.g. "$50K ARR per 1000 employees"
    demand_score: float
    clinical_importance: float
    evidence_count: int
    next_action: str  # specific sales action
    where_to_find: dict[str, list[str]]  # channels to reach this buyer type
    flags: list[str] = field(default_factory=list)


@dataclass
class SignalReport:
    """Pipeline intelligence report (serves both legacy and B2B views)."""
    generated_at: datetime
    total_topics: int
    fertility_topics: int
    audience_signals: list[AudienceSignal]
    by_struggle: dict[str, list[AudienceSignal]]
    evidence_gaps: list[dict]
    summary: str
    campaign_brief: str
    # B2B extensions (populated by generate_pipeline_intelligence)
    buyer_signals: list[BuyerSignal] = field(default_factory=list)
    by_buyer_type: dict[str, list[BuyerSignal]] = field(default_factory=dict)


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


def _build_buyer_signal(
    topic: TopicNode, score: TopicOpportunityScore, evidence_count: int,
    buyer_type: str = "chro",
) -> BuyerSignal:
    """Turn a scored fertility topic into a B2B buyer signal."""
    from fertility_sense.outreach.composer import _BUYER_CONTEXT

    pain_point = _buyer_pain_for_topic(topic.topic_id)
    buyer_context = _BUYER_CONTEXT.get(buyer_type, "Benefits decision-maker")

    # Determine sales motion based on buyer type
    sales_motion_map = {
        "chro": "outbound",
        "broker": "broker_enablement",
        "smb": "outbound",
        "union": "rfp_response",
        "tpa": "integration_partnership",
        "partner": "strategic_partnership",
    }
    sales_motion = sales_motion_map.get(buyer_type, "outbound")

    # Pipeline value estimate by buyer type
    value_map = {
        "chro": "$50K-500K ARR per enterprise",
        "broker": "$200K+ ARR via book of business",
        "smb": "$5K-25K ARR per company",
        "union": "$100K-1M ARR per union contract",
        "tpa": "$50K-200K ARR per TPA integration",
        "partner": "$500K+ ARR strategic deal",
    }
    pipeline_value = value_map.get(buyer_type, "$25K+ ARR")

    # Next action
    if evidence_count == 0:
        next_action = f"HOLD — need market data on {topic.display_name.lower()} before outreach"
    elif buyer_type == "broker":
        next_action = f"Send broker brief on {topic.display_name.lower()} — position for next RFP cycle"
    elif buyer_type == "chro":
        next_action = f"Send sales email + case study on {topic.display_name.lower()} — request 15-min call"
    elif buyer_type == "union":
        next_action = f"Prepare RFP response covering {topic.display_name.lower()} — include cost analysis"
    else:
        next_action = f"Create sales content: {topic.display_name.lower()} — target {buyer_type} buyers"

    where = _where_to_find_buyer(buyer_type)

    flags = []
    if score.unsafe_to_serve:
        flags.append("BLOCKED")
    if score.escalate_to_human:
        flags.append("NEEDS_REVIEW")
    if evidence_count == 0:
        flags.append("NO_EVIDENCE")

    return BuyerSignal(
        topic_id=topic.topic_id,
        display_name=topic.display_name,
        buyer_type=buyer_type,
        buyer_context=buyer_context,
        pain_point=pain_point,
        deal_stage="cold",
        sales_motion=sales_motion,
        pipeline_value_estimate=pipeline_value,
        demand_score=score.demand_score,
        clinical_importance=score.clinical_importance,
        evidence_count=evidence_count,
        next_action=next_action,
        where_to_find=where,
        flags=flags,
    )


def generate_pipeline_intelligence(pipe: Pipeline, top_n: int = 20) -> SignalReport:
    """Generate WIN Fertility pipeline intelligence report.

    Produces both legacy AudienceSignals and new BuyerSignals.
    ONLY includes preconception, trying, and fertility treatment stages.
    """
    all_scores = pipe.score(top_n=200)
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

    # Build legacy audience signals for top N
    signals: list[AudienceSignal] = []
    for s, topic in fertility_scores[:top_n]:
        ec = evidence_by_topic.get(s.topic_id, 0)
        signals.append(_build_signal(topic, s, ec))

    # Build B2B buyer signals — one per topic per primary buyer type
    buyer_signals: list[BuyerSignal] = []
    primary_buyer_types = ["chro", "broker", "smb"]
    for s, topic in fertility_scores[:top_n]:
        ec = evidence_by_topic.get(s.topic_id, 0)
        # Generate a signal for the primary buyer type (chro by default)
        buyer_signals.append(_build_buyer_signal(topic, s, ec, buyer_type="chro"))

    # Group by struggle type (journey stage) — legacy
    by_struggle: dict[str, list[AudienceSignal]] = {}
    for sig in signals:
        by_struggle.setdefault(sig.journey_stage, []).append(sig)

    # Group by buyer type
    by_buyer_type: dict[str, list[BuyerSignal]] = {}
    for bsig in buyer_signals:
        by_buyer_type.setdefault(bsig.buyer_type, []).append(bsig)

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

    # Pipeline brief
    actionable = [s for s in signals if "BLOCKED" not in s.flags and "NO_EVIDENCE" not in s.flags]

    brief_parts = [f"{len(signals)} pipeline opportunities identified."]
    if buyer_signals:
        chro_signals = [b for b in buyer_signals if b.buyer_type == "chro"]
        brief_parts.append(f"Enterprise targets ({len(chro_signals)} signals): {', '.join(b.display_name for b in chro_signals[:3])}.")
    if evidence_gaps:
        brief_parts.append(f"{len(evidence_gaps)} topics need market data before outreach.")

    summary = (
        f"{len(signals)} pipeline signals. "
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
        buyer_signals=buyer_signals,
        by_buyer_type=by_buyer_type,
    )


def generate_report(pipe: Pipeline, top_n: int = 20) -> SignalReport:
    """Generate a fertility-focused demand signal report.

    Backward-compatible entry point. Delegates to generate_pipeline_intelligence().
    ONLY includes preconception, trying, and fertility treatment stages.
    Pregnancy/postpartum/lactation topics are excluded.
    """
    return generate_pipeline_intelligence(pipe, top_n=top_n)


def format_report(report: SignalReport, as_json: bool = False) -> str:
    """Format for CLI display."""
    if as_json:
        data: dict = {
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
        }
        # Include buyer signals if present
        if report.buyer_signals:
            data["buyer_signals"] = [
                {
                    "topic": b.topic_id,
                    "buyer_type": b.buyer_type,
                    "buyer_context": b.buyer_context,
                    "pain_point": b.pain_point,
                    "deal_stage": b.deal_stage,
                    "sales_motion": b.sales_motion,
                    "pipeline_value": b.pipeline_value_estimate,
                    "demand": b.demand_score,
                    "clinical": b.clinical_importance,
                    "evidence": b.evidence_count,
                    "next_action": b.next_action,
                    "where": b.where_to_find,
                    "flags": b.flags,
                }
                for b in report.buyer_signals
            ]
        return json.dumps(data, indent=2)

    lines = []
    lines.append("=" * 90)
    lines.append("WIN FERTILITY — PIPELINE INTELLIGENCE")
    lines.append(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Fertility topics: {report.fertility_topics} of {report.total_topics} total")
    lines.append("=" * 90)
    lines.append("")
    lines.append("PIPELINE BRIEF")
    lines.append(report.campaign_brief)
    lines.append("")

    # B2B buyer signals section
    if report.buyer_signals:
        lines.append("-" * 90)
        lines.append("PIPELINE OPPORTUNITIES — BY BUYER TYPE")
        lines.append("-" * 90)
        for buyer_type, bsigs in report.by_buyer_type.items():
            lines.append(f"\n  [{buyer_type.upper()}]")
            for b in bsigs:
                flag_str = f" [{', '.join(b.flags)}]" if b.flags else ""
                lines.append(f"    {b.display_name} (demand={b.demand_score:.0f}, clinical={b.clinical_importance:.0f}){flag_str}")
                lines.append(f"      Pain Point:  {b.pain_point}")
                lines.append(f"      Next Action: {b.next_action}")
                lines.append(f"      Value:       {b.pipeline_value_estimate}")

    # Legacy audience signals section
    lines.append("")
    lines.append("-" * 90)
    lines.append("PIPELINE OPPORTUNITIES — BY STAGE")
    lines.append("-" * 90)
    for stage, sigs in report.by_struggle.items():
        lines.append(f"\n  [{stage}]")
        for s in sigs:
            flag_str = f" [{', '.join(s.flags)}]" if s.flags else ""
            lines.append(f"    {s.display_name} (demand={s.demand_score:.0f}, clinical={s.clinical_importance:.0f}){flag_str}")
            lines.append(f"      Struggle: {s.struggle}")
            lines.append(f"      Action:   {s.outreach_action}")
            # Only show consumer channels (Reddit) when no B2B buyer signals are available
            if not report.buyer_signals and s.where_to_find.get("subreddits"):
                lines.append(f"      Reddit:   {', '.join('r/' + sub for sub in s.where_to_find['subreddits'][:3])}")

    if report.evidence_gaps:
        lines.append("")
        lines.append("-" * 90)
        lines.append("DATA GAPS — Need market intelligence before outreach")
        lines.append("-" * 90)
        for gap in report.evidence_gaps:
            lines.append(f"  ! {gap['display_name']} ({gap['risk_tier']}) — {gap['action']}")

    lines.append("")
    lines.append("=" * 90)
    return "\n".join(lines)
