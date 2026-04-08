"""Campaign content composer — uses Claude to generate channel-specific content.

Takes a demand signal (topic + evidence + audience) and composes content
tailored for each distribution channel.
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
    """A piece of campaign content ready for distribution."""
    signal: AudienceSignal
    channel: str  # "reddit", "blog", "email", "social", "forum"
    title: str
    body: str
    cta: str  # Call to action
    hashtags: list[str] = field(default_factory=list)
    target_subreddits: list[str] = field(default_factory=list)
    evidence_citations: list[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    tone: str = "empathetic-expert"  # Warm, knowledgeable, never salesy


# Subreddit mapping by journey stage
_SUBREDDIT_MAP = {
    "Planning pregnancy": ["TryingForABaby", "WaitingForBaby"],
    "Actively trying to conceive": ["TryingForABaby", "TTC30"],
    "In fertility treatment (IVF/IUI)": ["infertility", "IVF"],
    "Early pregnancy (T1)": ["BabyBumps", "CautiousBB", "Pregnant"],
    "Mid pregnancy (T2)": ["BabyBumps", "Pregnant"],
    "Late pregnancy (T3)": ["BabyBumps", "Pregnant"],
    "Postpartum recovery": ["beyondthebump", "Postpartum"],
    "Breastfeeding": ["breastfeeding", "beyondthebump"],
}

# Channel-specific prompt templates
_CHANNEL_PROMPTS = {
    "reddit": """You are composing a helpful Reddit comment for someone asking about {topic}.

Target subreddit: r/{subreddit}
The person is: {who}
Their concern: {problem}

Evidence to reference:
{evidence}

Rules:
- Sound like a knowledgeable friend, NOT a corporation or doctor
- Use Reddit-native tone (casual, warm, empathetic)
- Share the evidence naturally ("I've read that studies show...")
- NEVER diagnose or recommend specific dosages
- End with encouragement and a gentle suggestion to talk to their doctor
- Include 1-2 relevant evidence citations naturally in the text
- Keep it under 200 words
- Do NOT use hashtags or marketing language
- Do NOT start with "As someone who..." or fake personal stories""",

    "blog": """Write a short evidence-backed blog section about {topic}.

Audience: {who}
Their concern: {problem}

Evidence:
{evidence}

Rules:
- Write 3-4 paragraphs, consumer-friendly language
- Cite sources inline as [Source, Year]
- Include a clear H2 heading
- End with a call to action to learn more or talk to a provider
- SEO-friendly but not keyword-stuffed
- Never diagnose, recommend dosages, or guarantee outcomes""",

    "email": """Write a brief, warm email paragraph about {topic} for a drip campaign.

Recipient profile: {who}
What they care about: {problem}

Evidence to weave in:
{evidence}

Rules:
- 2-3 sentences max
- Warm, personal tone (like a trusted friend who did the research)
- One evidence-backed insight they can use today
- End with a soft CTA ("Want to learn more about...?")
- Never diagnose or prescribe""",

    "social": """Write a social media post about {topic} for Instagram/Twitter.

Audience: {who}
Insight: {problem}

Evidence:
{evidence}

Rules:
- Under 280 characters for the main text
- Include 1 key evidence-backed fact
- Warm, empowering tone
- 3-5 relevant hashtags
- End with a question or invitation to engage
- Never medical advice""",

    "forum": """Write a helpful forum response for someone asking about {topic}.

Context: {who} in a fertility/pregnancy community
Their question/concern: {problem}

Evidence:
{evidence}

Rules:
- Empathetic, knowledgeable tone
- Share evidence naturally without lecturing
- Acknowledge their feelings first, then share what you know
- Under 150 words
- Suggest talking to their provider for personal guidance
- No marketing, no selling""",
}


def _build_evidence_context(evidence: list[EvidenceRecord], max_records: int = 3) -> str:
    """Format evidence records for prompt injection."""
    if not evidence:
        return "(No specific evidence records available — use general knowledge)"
    lines = []
    for r in evidence[:max_records]:
        findings = "; ".join(r.key_findings) if r.key_findings else "No specific findings extracted"
        lines.append(f"- [{r.source_feed}, {r.publication_date}] {r.title}: {findings}")
    return "\n".join(lines)


def compose_campaign_content(
    signal: AudienceSignal,
    channel: str,
    topic: TopicNode,
    evidence: list[EvidenceRecord],
    dispatcher: "AgentDispatcher | None" = None,
) -> CampaignContent:
    """Compose campaign content for a specific channel.

    Uses the product-translator agent via dispatcher when available,
    falls back to template-based composition when offline.
    """
    evidence_text = _build_evidence_context(evidence)
    subreddits = _SUBREDDIT_MAP.get(signal.journey_stage, ["TryingForABaby"])
    citations = [f"[{r.source_feed}, {r.publication_date}]" for r in evidence[:3]]

    prompt_template = _CHANNEL_PROMPTS.get(channel, _CHANNEL_PROMPTS["blog"])
    prompt = prompt_template.format(
        topic=topic.display_name,
        who=signal.who,
        problem=signal.problem,
        evidence=evidence_text,
        subreddit=subreddits[0] if subreddits else "TryingForABaby",
    )

    # Use Claude if dispatcher available
    title = ""
    body = ""
    cta = ""
    hashtags: list[str] = []

    if dispatcher:
        result = dispatcher.dispatch(
            agent_name="product-translator",
            skill_name="content-brief",
            prompt=prompt,
        )
        if result.status == "completed":
            body = result.output
        else:
            body = f"[offline] Content for {channel}: {topic.display_name}"
    else:
        body = f"[offline] {channel} content about {topic.display_name} for {signal.who}"

    # Extract or generate title
    if channel == "blog":
        title = f"What to Know About {topic.display_name}: An Evidence-Based Guide"
    elif channel == "email":
        title = f"Quick insight: {topic.display_name}"
    elif channel == "social":
        title = topic.display_name
        hashtags = [
            f"#fertility", f"#{topic.topic_id.replace('-', '')}",
            "#ttc", "#fertilitytips", "#reproductive health",
        ]
    elif channel == "reddit":
        title = ""  # Reddit comments don't have titles
    elif channel == "forum":
        title = ""

    cta = f"Learn more about {topic.display_name.lower()} at our resource center"

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
