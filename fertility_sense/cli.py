"""CLI interface for fertility-sense."""

from __future__ import annotations

import json
import uuid

import click

from fertility_sense import __version__


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Fertility-Sense: Demand-sensing intelligence platform."""


def _pipeline() -> "Pipeline":
    """Lazy-create a Pipeline instance."""
    from fertility_sense.config import FertilitySenseConfig
    from fertility_sense.pipeline import Pipeline

    return Pipeline(FertilitySenseConfig())


@main.command()
@click.option("--feed", default="all", help="Feed name or 'all'")
def ingest(feed: str) -> None:
    """Trigger feed ingestion and store results."""
    pipe = _pipeline()
    click.echo(f"Ingesting feed: {feed}")
    click.echo(f"  {len(pipe.registry)} feed(s) registered")

    try:
        summary = pipe.ingest(feed)
        total = sum(summary.values())
        for fname, count in summary.items():
            click.echo(f"  {fname}: {count} records")
        click.echo(f"Ingestion complete — {total} total records stored.")
    except KeyError:
        click.echo(f"  Error: feed '{feed}' not found. Available: "
                    f"{', '.join(f.name for f in pipe.registry.all_feeds())}")
    except Exception as e:
        click.echo(f"  Error: {e}")


@main.command()
@click.option("--topic", default="all", help="Topic ID or 'all'")
@click.option("--top", default=20, type=int, help="Show top N topics")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def score(topic: str, top: int, as_json: bool) -> None:
    """Compute Topic Opportunity Scores."""
    pipe = _pipeline()
    scores = pipe.score(topic_id=topic, top_n=top)

    if not scores:
        click.echo("No topics found.")
        return

    if as_json:
        click.echo(json.dumps([s.model_dump(mode="json") for s in scores], indent=2))
        return

    # Table output
    click.echo(f"{'Rank':<6} {'Topic':<35} {'TOS':>6} {'Demand':>7} {'Clinical':>9} {'Trust':>6} {'Comm':>6} {'Flags'}")
    click.echo("-" * 95)
    for s in scores:
        flags = []
        if s.unsafe_to_serve:
            flags.append("BLOCKED")
        if s.escalate_to_human:
            flags.append("ESCALATE")
        flag_str = ",".join(flags) if flags else ""
        rank = s.rank or "-"
        click.echo(
            f"{rank:<6} {s.topic_id:<35} {s.composite_tos:>6.1f} "
            f"{s.demand_score:>7.1f} {s.clinical_importance:>9.1f} "
            f"{s.trust_risk_score:>6.1f} {s.commercial_fit:>6.1f} {flag_str}"
        )


@main.command()
@click.option("--topic", required=True, help="Topic ID")
@click.option("--query", required=True, help="User query")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def answer(topic: str, query: str, as_json: bool) -> None:
    """Assemble a governed answer with real evidence."""
    pipe = _pipeline()

    try:
        result = pipe.answer(topic, query)
    except ValueError as e:
        click.echo(f"Error: {e}")
        return

    if as_json:
        click.echo(result.model_dump_json(indent=2))
        return

    click.echo(f"Topic:      {result.topic_id}")
    click.echo(f"Risk Tier:  {result.risk_tier.value}")
    click.echo(f"Template:   {result.template_used}")
    click.echo(f"Status:     {result.governance_status}")
    if result.escalation_reason:
        click.echo(f"Escalation: {result.escalation_reason}")
    click.echo(f"Evidence:   {len(result.provenance.evidence_ids)} record(s)")
    click.echo(f"Grade:      {result.provenance.grade.value}")
    click.echo(f"Sources:    {', '.join(result.provenance.sources) or 'none'}")
    click.echo()
    for section_name, text in result.sections.items():
        click.echo(f"--- {section_name} ---")
        click.echo(text)
        click.echo()


@main.command()
@click.option("--all", "show_all", is_flag=True, help="Show all status")
@click.option("--feeds", is_flag=True, help="Show feed status")
@click.option("--agents", is_flag=True, help="Show agent status")
def status(show_all: bool, feeds: bool, agents: bool) -> None:
    """Show pipeline health status."""
    pipe = _pipeline()
    health = pipe.health()

    if show_all or feeds:
        click.echo("=== Feed Health ===")
        click.echo(f"  Registered: {health['feeds']}")
        for fd in health.get("feed_details", []):
            stale = " (STALE)" if fd["is_stale"] else ""
            click.echo(f"  {fd['name']:<25} {fd['records']} records{stale}")

    if show_all or agents:
        click.echo("=== Agent Status ===")
        from fertility_sense.nemoclaw.agents import ALL_AGENTS

        for agent in ALL_AGENTS:
            tier = agent.default_tier.value.split("-")[1]
            click.echo(
                f"  {agent.name:<25} {agent.role.value:<10} {tier:<8} "
                f"({len(agent.skills)} skills)"
            )

    if show_all:
        click.echo("=== Data ===")
        click.echo(f"  Topics:           {health['topics']}")
        click.echo(f"  Evidence records: {health['evidence_records']}")
        click.echo(f"  Safety alerts:    {health['safety_alerts_active']}")

    if not (show_all or feeds or agents):
        click.echo("Use --all, --feeds, or --agents")


@main.command()
@click.option("--top", default=20, type=int, help="Top N topics")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def report(top: int, as_json: bool) -> None:
    """Generate actionable demand signal report for campaign planning."""
    from fertility_sense.report import format_report, generate_report

    pipe = _pipeline()
    rpt = generate_report(pipe, top_n=top)
    click.echo(format_report(rpt, as_json=as_json))


@main.command()
@click.option("--top", default=5, type=int, help="Top N signals to campaign on")
@click.option("--channel", multiple=True, help="Channels (reddit, blog, email, social, forum)")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON")
def campaign(top: int, channel: tuple[str, ...], as_json: bool) -> None:
    """Generate multi-channel campaign content from demand signals."""
    from fertility_sense.outreach.campaign import format_campaign_plan, generate_campaign_plan

    pipe = _pipeline()
    channels = list(channel) if channel else None
    click.echo(f"Generating campaigns for top {top} signals...")
    plan = generate_campaign_plan(pipe, top_n=top, channels=channels)
    click.echo(format_campaign_plan(plan, as_json=as_json))


@main.command("send-email")
@click.option("--to", required=True, help="Recipient email address")
@click.option("--top", default=3, type=int, help="Top N signals to include")
@click.option("--subject", default=None, help="Email subject (auto-generated if omitted)")
def send_email(to: str, top: int, subject: str | None) -> None:
    """Send campaign report email to a recipient."""
    from fertility_sense.outreach.campaign import generate_campaign_plan
    from fertility_sense.outreach.email_sender import EmailSender, campaign_to_email

    pipe = _pipeline()
    config = pipe.config

    sender = EmailSender(config)
    click.echo(f"Connecting to {config.smtp_host}...")

    if not sender.test_connection():
        click.echo("SMTP connection failed. Check email credentials in .env")
        return

    plan = generate_campaign_plan(pipe, top_n=top, channels=["email"])

    body_parts = [
        "Fertility Sense — Demand Signal Report\n",
        f"{plan.total_content_pieces} campaign emails from top {top} demand signals.\n",
    ]
    for i, camp in enumerate(plan.campaigns, 1):
        sig = camp.signal
        body_parts.append(f"---\n\n{i}. {sig.display_name}")
        body_parts.append(f"Audience: {sig.who}")
        body_parts.append(f"Demand: {sig.demand_score:.0f} | Clinical: {sig.clinical_importance:.0f}\n")
        for content in camp.content:
            body_parts.append(content.body)
        body_parts.append("")

    subj = subject or f"Fertility Sense — Top {top} Campaign Signals"
    email = campaign_to_email(to=to, subject=subj, body="\n".join(body_parts))
    result = sender.send(email)

    if result.status == "sent":
        click.echo(f"Sent to {to} at {result.sent_at}")
    else:
        click.echo(f"Failed: {result.error}")


@main.command("check-inbox")
@click.option("--limit", default=10, type=int, help="Number of messages to show")
def check_inbox(limit: int) -> None:
    """Check the fertility inbox for replies."""
    from fertility_sense.outreach.email_sender import EmailSender

    pipe = _pipeline()
    sender = EmailSender(pipe.config)
    messages = sender.check_inbox(limit=limit)

    if not messages:
        click.echo("No messages found.")
        return

    click.echo(f"=== Inbox ({len(messages)} messages) ===")
    for msg in messages:
        click.echo(f"  From: {msg.from_addr}")
        click.echo(f"  Subject: {msg.subject}")
        click.echo(f"  Date: {msg.date}")
        click.echo()


@main.command()
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", default="", help="Anthropic API key")
def pipeline(api_key: str) -> None:
    """Run the full intelligence pipeline."""
    pipe = _pipeline()
    run_id = str(uuid.uuid4())[:8]
    click.echo(f"Running pipeline (run_id={run_id})...")

    if pipe.server._client:
        click.echo(f"  Claude client: LIVE (budget=${pipe.config.cost_budget_usd:.2f})")
    else:
        click.echo("  Claude client: OFFLINE (no API key or SDK)")

    result = pipe.run_full(run_id)
    click.echo(f"Pipeline {result['status']}:")
    for phase in result["phases"]:
        click.echo(f"  {phase['phase']}: {phase['status']} ({', '.join(phase['agents'])})")


if __name__ == "__main__":
    main()
