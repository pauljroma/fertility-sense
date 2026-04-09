"""Campaign generator — turns signal report into multi-channel campaign plan.

Takes the top demand signals and generates a complete campaign with
content for each channel, ready for review and distribution.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from fertility_sense.outreach.composer import CampaignContent, compose_campaign_content
from fertility_sense.pipeline import Pipeline
from fertility_sense.report import AudienceSignal, generate_report

if TYPE_CHECKING:
    from fertility_sense.nemoclaw.dispatcher import AgentDispatcher
    from fertility_sense.outreach.content_queue import ContentQueue

logger = logging.getLogger(__name__)

# Default channels for each action type
_ACTION_CHANNELS = {
    "content": ["blog", "social", "reddit", "email"],
    "tool": ["blog", "social", "email"],
    "referral": ["reddit", "forum", "email", "social"],
    "commerce": ["blog", "social", "email"],
    "investigate": [],  # Don't campaign on unvalidated topics
}


@dataclass
class Campaign:
    """A multi-channel campaign for a single demand signal."""
    signal: AudienceSignal
    content: list[CampaignContent] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def channels(self) -> list[str]:
        return [c.channel for c in self.content]


@dataclass
class CampaignPlan:
    """Complete campaign plan across multiple signals."""
    campaigns: list[Campaign]
    total_signals: int
    total_content_pieces: int
    generated_at: datetime = field(default_factory=datetime.utcnow)
    summary: str = ""


def generate_campaign_plan(
    pipe: Pipeline,
    top_n: int = 10,
    channels: list[str] | None = None,
) -> CampaignPlan:
    """Generate a campaign plan from the top demand signals.

    Args:
        pipe: Pipeline instance with loaded data.
        top_n: Number of top signals to campaign on.
        channels: Override channel list. Default: auto from action type.
    """
    report = generate_report(pipe, top_n=top_n)
    dispatcher = pipe.server.dispatcher

    campaigns: list[Campaign] = []
    total_pieces = 0

    for signal in report.audience_signals:
        # Skip blocked or evidence-free signals
        if "BLOCKED" in signal.flags:
            continue
        if "NO_EVIDENCE" in signal.flags and signal.risk_tier != "green":
            continue

        topic = pipe.graph.get_topic(signal.topic_id)
        if topic is None:
            continue

        evidence = pipe.evidence_store.by_topic(signal.topic_id)

        # Determine channels
        if channels:
            target_channels = channels
        else:
            target_channels = _ACTION_CHANNELS.get(signal.outreach_type.split(" ")[0].lower(), ["blog"])
            # Reddit comments only make sense for non-clinical topics
            if signal.risk_tier in ("red", "black") and "reddit" in target_channels:
                target_channels = [c for c in target_channels if c != "reddit"]

        # Generate content for each channel
        campaign = Campaign(signal=signal)
        for channel in target_channels:
            content = compose_campaign_content(
                signal=signal,
                channel=channel,
                topic=topic,
                evidence=evidence,
                dispatcher=dispatcher,
            )
            campaign.content.append(content)
            total_pieces += 1

        campaigns.append(campaign)

    summary = (
        f"{len(campaigns)} campaigns across {total_pieces} content pieces. "
        f"Channels: {', '.join(sorted({c.channel for camp in campaigns for c in camp.content}))}."
    )

    return CampaignPlan(
        campaigns=campaigns,
        total_signals=len(report.audience_signals),
        total_content_pieces=total_pieces,
        summary=summary,
    )


def queue_campaign(plan: CampaignPlan, queue: "ContentQueue") -> int:
    """Add all campaign content pieces to the review queue.

    Returns the number of items queued.
    """
    from fertility_sense.outreach.content_queue import QueueItem

    count = 0
    for campaign in plan.campaigns:
        for content in campaign.content:
            # Determine target: first subreddit for reddit, otherwise generic
            if content.channel == "reddit" and content.target_subreddits:
                target = f"r/{content.target_subreddits[0]}"
            elif content.channel in ("email", "direct_email"):
                target = "email-list"
            elif content.channel == "blog":
                target = campaign.signal.topic_id
            else:
                target = content.channel

            item = QueueItem(
                channel=content.channel,
                topic_id=campaign.signal.topic_id,
                title=content.title,
                body=content.body,
                target=target,
                risk_tier=campaign.signal.risk_tier,
                evidence_count=campaign.signal.evidence_count,
            )
            queue.add(item)
            count += 1
    return count


def format_campaign_plan(plan: CampaignPlan, as_json: bool = False) -> str:
    """Format a CampaignPlan for display."""
    if as_json:
        return json.dumps({
            "generated_at": plan.generated_at.isoformat(),
            "summary": plan.summary,
            "total_signals": plan.total_signals,
            "total_content_pieces": plan.total_content_pieces,
            "campaigns": [
                {
                    "topic": c.signal.topic_id,
                    "display_name": c.signal.display_name,
                    "who": c.signal.who,
                    "channels": [
                        {
                            "channel": content.channel,
                            "title": content.title,
                            "body": content.body[:500],
                            "cta": content.cta,
                            "subreddits": content.target_subreddits,
                            "hashtags": content.hashtags,
                            "citations": content.evidence_citations,
                        }
                        for content in c.content
                    ],
                }
                for c in plan.campaigns
            ],
        }, indent=2)

    lines = []
    lines.append("=" * 90)
    lines.append("FERTILITY-SENSE CAMPAIGN PLAN")
    lines.append(f"Generated: {plan.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(plan.summary)
    lines.append("=" * 90)

    for i, campaign in enumerate(plan.campaigns, 1):
        sig = campaign.signal
        lines.append("")
        lines.append(f"{'─' * 90}")
        lines.append(f"CAMPAIGN {i}: {sig.display_name}")
        lines.append(f"  Audience:  {sig.who}")
        lines.append(f"  Struggle:  {sig.struggle}")
        lines.append(f"  Demand:    {sig.demand_score:.0f} | Clinical: {sig.clinical_importance:.0f}")
        lines.append(f"  Evidence:  {sig.evidence_count} record(s)")
        lines.append(f"  Channels:  {', '.join(campaign.channels)}")

        for content in campaign.content:
            lines.append("")
            lines.append(f"  [{content.channel.upper()}]")
            if content.title:
                lines.append(f"  Title: {content.title}")
            if content.target_subreddits and content.channel == "reddit":
                lines.append(f"  Subreddits: {', '.join('r/' + s for s in content.target_subreddits)}")
            if content.hashtags:
                lines.append(f"  Tags: {' '.join(content.hashtags)}")

            # Show body (truncate for display)
            body_lines = content.body.strip().split("\n")
            for bl in body_lines[:15]:
                lines.append(f"    {bl}")
            if len(body_lines) > 15:
                lines.append(f"    ... ({len(body_lines) - 15} more lines)")

            if content.evidence_citations:
                lines.append(f"  Sources: {', '.join(content.evidence_citations)}")

    lines.append("")
    lines.append("=" * 90)
    return "\n".join(lines)
