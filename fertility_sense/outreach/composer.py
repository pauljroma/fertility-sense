"""Campaign content composer — generates channel-specific B2B sales content.

WIN Fertility B2B sales content for:
- CHROs at 1000+ employee enterprises (Disney, Nvidia, JPM scale)
- Brokers at Willis/AON/Marsh evaluating fertility solutions
- HR leads at small companies (50-500 employees)
- Benefits directors at labor unions
- Integration managers at third-party administrators
- Strategic partners / private equity stakeholders (Blackstone)

Value prop: best treatment at lowest cost via managed network of
fertility doctors, mental health counselors, and drug companies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from fertility_sense.models.evidence import EvidenceRecord
from fertility_sense.models.topic import TopicNode
from fertility_sense.report import AudienceSignal

if TYPE_CHECKING:
    from fertility_sense.nemoclaw.dispatcher import AgentDispatcher

logger = logging.getLogger(__name__)


@dataclass
class CampaignContent:
    """A piece of B2B sales content ready for distribution."""
    signal: AudienceSignal
    channel: str
    title: str
    body: str
    cta: str
    hashtags: list[str] = field(default_factory=list)
    target_subreddits: list[str] = field(default_factory=list)
    evidence_citations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Buyer context — who we are selling to
_BUYER_CONTEXT = {
    "chro": "VP Benefits / CHRO at a 1000+ employee enterprise",
    "broker": "Producer at Willis/AON/Marsh evaluating fertility solutions for clients",
    "smb": "HR lead or managing partner at a small company (50-500 employees)",
    "union": "Benefits director at a labor union",
    "tpa": "Integration manager at a third-party administrator",
    "partner": "Strategic partner / private equity stakeholder",
}

_CHANNEL_PROMPTS = {
    "linkedin": """You are writing executive thought leadership for LinkedIn on behalf of WIN Fertility.

Topic: {topic}
Buyer: {who}
Their pain point: {struggle}

Evidence:
{evidence}

RULES:
- Write as an authoritative partner, NOT an empathetic friend
- Address CHROs, brokers, and benefits leaders directly
- Reference WIN's managed network of fertility doctors, mental health counselors, and Rx partners with negotiated discounts
- Lead with ROI and data: cost reduction, retention lift, PMPM savings
- Reference enterprise scale where relevant (Disney, Nvidia, JPM)
- Core message: "best treatment at lowest cost"
- Address the buyer's pain: rising fertility benefit costs, network quality gaps, employee retention
- End with a clear insight or question that drives engagement
- Under 300 words
- 3-5 hashtags: #FertilityBenefits #HRLeadership #EmployeeBenefits etc.
- No consumer emotional language — this is B2B""",

    "sales_email": """You are writing an outbound B2B sales email on behalf of WIN Fertility.

Recipient: {who}
Topic: {topic}
Their pain point: {struggle}

Evidence:
{evidence}

RULES:
- Concise, direct, executive tone — 3-5 sentences max
- Open with a data point or pain point the buyer will recognize
- Reference WIN's managed network advantage: fertility doctors, mental health counselors, and Rx partners with negotiated discounts
- Deliver the value prop: "best treatment at lowest cost"
- Quantify where possible: cost per cycle savings, PMPM impact, retention ROI
- Reference WIN's enterprise client base (Disney, Nvidia, JPM) for credibility
- CTA: propose a 15-minute call, a custom ROI analysis, or a broker brief
- No consumer language, no "we know how hard this is" — this is about delivering business outcomes
- Under 150 words""",

    "case_study": """You are writing a B2B customer success story for WIN Fertility.

Topic: {topic}
Target reader: {who}
Their pain point: {struggle}

Evidence:
{evidence}

RULES:
- Structure: Challenge > Solution > Results
- Reference enterprise-scale deployments (Disney, Nvidia, JPM)
- Quantify outcomes: cost per cycle reduction, PMPM savings, utilization rates, employee satisfaction scores
- Highlight WIN's managed network: fertility doctors, mental health counselors, drug company partnerships with negotiated discounts
- Show how WIN delivered "best treatment at lowest cost"
- Include a quote-ready line an HR leader would say
- Address the reader's pain: "If your organization faces similar cost pressures..."
- 3-4 paragraphs, data-heavy, no emotional consumer language
- End with a bridge to the reader's situation""",

    "broker_brief": """You are writing a one-pager for broker producers (Willis, AON, Marsh) on behalf of WIN Fertility.

Topic: {topic}
Audience: {who}
Their pain point: {struggle}

Evidence:
{evidence}

RULES:
- Structure: Market Problem > WIN Solution > Differentiators > How to Position
- Lead with the broker's pain: client RFP requirements, competitive differentiation, client retention
- Highlight WIN's managed network of fertility doctors, mental health counselors, and Rx partners
- Quantify: cost per cycle vs. market average, PMPM impact, client satisfaction metrics
- Position WIN as the broker's competitive advantage: "best treatment at lowest cost"
- Include 2-3 bullet points a broker can use in client conversations
- Reference enterprise logos (Disney, Nvidia, JPM) as proof points
- Under 250 words, scannable format with headers
- No consumer language — this is a sales enablement tool""",

    "rfp_response": """You are drafting a structured RFP response section for WIN Fertility.

Topic: {topic}
RFP evaluator: {who}
Their requirement: {struggle}

Evidence:
{evidence}

RULES:
- Formal, precise, compliance-ready tone
- Structure: Requirement > WIN's Approach > Evidence > Differentiator
- Reference WIN's managed network: fertility doctors (500+ clinics), mental health counselors, Rx partnerships
- Quantify outcomes: clinical success rates, cost savings vs. market, member satisfaction
- Address specific RFP criteria: network adequacy, quality metrics, cost containment, mental health support
- Highlight WIN's value prop: "best treatment at lowest cost through managed network"
- Reference enterprise deployments for credibility (Disney, Nvidia, JPM)
- Include data citations where available
- Under 300 words, structured with clear headers""",

    "conference": """You are writing talking points for a WIN Fertility speaker at a benefits conference (SHRM, HLTH, broker summit).

Topic: {topic}
Audience: {who}
Their pain point: {struggle}

Evidence:
{evidence}

RULES:
- 5-7 bullet points, each a standalone talking point
- Lead with market data: fertility benefit demand is rising, costs are accelerating, network quality varies
- Position WIN's managed network as the solution: fertility doctors, mental health counselors, Rx partnerships
- Reference enterprise clients (Disney, Nvidia, JPM) as social proof
- Each point should land the value prop: "best treatment at lowest cost"
- Include one contrarian insight that challenges conventional thinking about fertility benefits
- Address the audience's pain: cost control, talent retention, broker differentiation, RFP wins
- End with a clear call-to-action point
- No consumer emotional language — this is a room full of decision-makers""",
}


def _build_evidence_context(evidence: list[EvidenceRecord], max_records: int = 3) -> str:
    if not evidence:
        return "(No specific evidence records — use general fertility benefits industry knowledge)"
    lines = []
    for r in evidence[:max_records]:
        findings = "; ".join(r.key_findings) if r.key_findings else "No specific findings"
        lines.append(f"- [{r.source_feed}, {r.publication_date}] {r.title}: {findings}")
    return "\n".join(lines)


def compose_campaign_content(
    signal: AudienceSignal,
    channel: str,
    topic: TopicNode,
    evidence: list[EvidenceRecord],
    dispatcher: "AgentDispatcher | None" = None,
) -> CampaignContent:
    """Compose B2B sales content for a specific channel."""
    evidence_text = _build_evidence_context(evidence)

    # Determine buyer context from signal or fall back to default
    buyer_type = getattr(signal, "buyer_type", None) or ""
    buyer_context = _BUYER_CONTEXT.get(buyer_type, "Benefits decision-maker evaluating fertility solutions")

    citations = [f"[{r.source_feed}, {r.publication_date}]" for r in evidence[:3]]

    prompt_template = _CHANNEL_PROMPTS.get(channel, _CHANNEL_PROMPTS["sales_email"])

    # Build format kwargs — use signal.who/struggle if available, add buyer context
    who_str = signal.who if signal.who else buyer_context
    struggle_str = signal.struggle if signal.struggle else "Rising fertility benefit costs and network quality gaps"

    prompt = prompt_template.format(
        topic=topic.display_name,
        who=who_str,
        struggle=struggle_str,
        evidence=evidence_text,
    )

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
            body = f"[offline] {channel} content: {topic.display_name}"
    else:
        body = f"[offline] {channel} content about {topic.display_name} for {who_str}"

    # Channel-specific metadata
    title = ""
    hashtags: list[str] = []
    if channel == "case_study":
        title = f"{topic.display_name}: How WIN Delivers Results at Enterprise Scale"
    elif channel == "sales_email":
        title = f"Reducing fertility benefit costs: {topic.display_name.lower()}"
    elif channel == "linkedin":
        title = f"{topic.display_name}: What the Data Shows for Benefits Leaders"
        hashtags = ["#FertilityBenefits", "#HRLeadership", "#EmployeeBenefits",
                     f"#{topic.topic_id.replace('-', '')}", "#WINFertility"]
    elif channel == "broker_brief":
        title = f"WIN Fertility Broker Brief: {topic.display_name}"
    elif channel == "rfp_response":
        title = f"RFP Response: {topic.display_name}"
    elif channel == "conference":
        title = f"Conference Talking Points: {topic.display_name}"

    cta = f"Schedule a 15-minute call to discuss {topic.display_name.lower()}"

    # Preserve target_subreddits for backward compat (empty for B2B channels)
    subreddits: list[str] = []

    return CampaignContent(
        signal=signal,
        channel=channel,
        title=title,
        body=body,
        cta=cta,
        hashtags=hashtags,
        target_subreddits=subreddits,
        evidence_citations=citations,
    )
