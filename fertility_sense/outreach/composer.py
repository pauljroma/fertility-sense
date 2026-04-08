"""Campaign content composer — generates channel-specific fertility outreach.

Every piece of content is for people STRUGGLING WITH FERTILITY:
- TTC (trying to conceive) couples
- People with infertility diagnoses
- Those exploring or undergoing treatment (IVF/IUI/ART)
- Men and women investigating reproductive health
- People dealing with the emotional toll of infertility

NOT for pregnancy/postpartum audiences.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from fertility_sense.models.evidence import EvidenceRecord
from fertility_sense.models.topic import TopicNode
from fertility_sense.report import AudienceSignal

if TYPE_CHECKING:
    from fertility_sense.nemoclaw.dispatcher import AgentDispatcher

logger = logging.getLogger(__name__)


@dataclass
class CampaignContent:
    """A piece of outreach content ready for distribution."""
    signal: AudienceSignal
    channel: str
    title: str
    body: str
    cta: str
    hashtags: list[str] = field(default_factory=list)
    target_subreddits: list[str] = field(default_factory=list)
    evidence_citations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


# Subreddit mapping — fertility-focused only
_SUBREDDIT_MAP = {
    "Optimizing fertility before trying": ["TryingForABaby", "WaitingForBaby", "TTC_PCOS"],
    "Actively trying to conceive (TTC)": ["TryingForABaby", "TTC30", "stilltrying", "maleinfertility"],
    "Undergoing fertility treatment (IVF/IUI/ART)": ["infertility", "IVF", "InfertilityBabies", "maleinfertility"],
}

_CHANNEL_PROMPTS = {
    "reddit": """You are writing a helpful Reddit reply for someone in a fertility community.

Target: r/{subreddit}
This person is: {who}
Their struggle: {struggle}

Evidence:
{evidence}

CRITICAL RULES:
- This person is struggling to conceive. Be empathetic FIRST.
- Sound like someone who's been through it, not a company
- Share evidence naturally ("research shows..." not "according to our data...")
- NEVER be salesy, promotional, or use marketing language
- NEVER diagnose or recommend specific dosages
- Acknowledge the emotional difficulty — infertility is hard
- If relevant, mention both male and female factors
- End with genuine encouragement + suggest talking to their RE/OB
- Under 200 words
- No hashtags, no links, no self-promotion""",

    "blog": """Write a fertility-focused blog section about {topic}.

Audience: {who}
Their struggle: {struggle}

Evidence:
{evidence}

RULES:
- Write for people actively trying to conceive or dealing with infertility
- 3-4 paragraphs, warm but evidence-backed
- Cite sources as [Source, Year]
- Address both partners where relevant (male + female fertility)
- Acknowledge the emotional weight without being preachy
- End with actionable next steps + "talk to your RE/fertility specialist"
- SEO-friendly H2 heading
- Never diagnose or guarantee outcomes""",

    "email": """Write a short, warm email for someone dealing with fertility challenges.

Recipient: {who}
Their struggle: {struggle}

Evidence:
{evidence}

RULES:
- 2-3 sentences, like a message from a knowledgeable friend
- One evidence-backed insight they can use or feel reassured by
- Acknowledge the difficulty — don't be chirpy or dismissive
- Soft CTA: "Want to learn more about...?" or "We put together a guide on..."
- Never diagnose, prescribe, or promise results
- This is someone who may have been trying for months or years — be sensitive""",

    "social": """Write a social media post about {topic} for the fertility community.

Audience: {who}
Context: {struggle}

Evidence:
{evidence}

RULES:
- Under 280 characters main text
- One evidence-backed fertility fact
- Empathetic, empowering tone — never dismissive of the struggle
- Address TTC community directly
- 3-5 hashtags: #TTC #fertility #infertility etc.
- End with a question to drive engagement
- No medical advice, no outcome promises""",

    "forum": """Write a supportive reply for someone in a fertility forum.

Person: {who}
Their struggle: {struggle}

Evidence:
{evidence}

RULES:
- Lead with empathy — acknowledge how hard this is
- Share one helpful evidence-based insight
- Be the person in the forum who actually did the research
- Under 150 words
- Suggest they bring it up with their fertility doctor/RE
- No selling, no links, no self-promotion""",

    "direct_email": """Write a personal outreach email to someone who has shown interest in fertility topics.

Their profile: {who}
What they're researching: {struggle}

Evidence:
{evidence}

RULES:
- Personal, warm, like you're checking in
- Reference what they've been looking at
- Share one genuinely useful evidence-backed insight
- Offer to help: "I put together some resources on this..." or "Happy to share what we've found..."
- This is relationship-building, not selling
- Never diagnose or prescribe
- Under 100 words""",
}


def _build_evidence_context(evidence: list[EvidenceRecord], max_records: int = 3) -> str:
    if not evidence:
        return "(No specific evidence records — use general fertility knowledge)"
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
    """Compose fertility outreach content for a specific channel."""
    evidence_text = _build_evidence_context(evidence)
    subreddits = _SUBREDDIT_MAP.get(signal.journey_stage, ["TryingForABaby", "infertility"])
    citations = [f"[{r.source_feed}, {r.publication_date}]" for r in evidence[:3]]

    prompt_template = _CHANNEL_PROMPTS.get(channel, _CHANNEL_PROMPTS["blog"])
    prompt = prompt_template.format(
        topic=topic.display_name,
        who=signal.who,
        struggle=signal.struggle,
        evidence=evidence_text,
        subreddit=subreddits[0] if subreddits else "TryingForABaby",
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
        body = f"[offline] {channel} content about {topic.display_name} for {signal.who}"

    # Channel-specific metadata
    title = ""
    hashtags: list[str] = []
    if channel == "blog":
        title = f"{topic.display_name}: What the Research Actually Shows"
    elif channel in ("email", "direct_email"):
        title = f"Something useful about {topic.display_name.lower()}"
    elif channel == "social":
        title = topic.display_name
        hashtags = ["#TTC", "#fertility", "#infertility", f"#{topic.topic_id.replace('-', '')}", "#fertilitytips"]

    cta = f"Learn more about {topic.display_name.lower()}"

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
