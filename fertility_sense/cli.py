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


@main.command()
@click.option("--once", is_flag=True, help="Run scout once")
@click.option("--loop", is_flag=True, help="Run continuous loop")
@click.option("--interval", default=6.0, type=float, help="Hours between loop runs")
def scout(once: bool, loop: bool, interval: float) -> None:
    """Run autonomous demand-sensing scout."""
    from fertility_sense.agents.scout_loop import ScoutLoop

    pipe = _pipeline()
    sl = ScoutLoop(pipe)

    if loop:
        click.echo(f"Starting scout loop (interval={interval}h). Press Ctrl+C to stop.")
        try:
            sl.run_loop(interval_hours=interval)
        except KeyboardInterrupt:
            click.echo("\nScout loop stopped.")
        return

    # Default to --once behavior
    click.echo("Running scout...")
    result = sl.run_once()
    click.echo(f"Status: {result.status}")
    click.echo(f"Topics scored: {result.topics_scored}")
    click.echo(f"Feeds ingested: {result.feeds_ingested}")
    if result.velocity_alerts:
        click.echo(f"Velocity alerts: {len(result.velocity_alerts)}")
        for alert in result.velocity_alerts:
            arrow = "^" if alert.direction == "rising" else "v"
            click.echo(
                f"  {arrow} {alert.topic_id}: {alert.previous_tos} -> "
                f"{alert.current_tos} ({alert.delta:+.1f})"
            )
    else:
        click.echo("No velocity alerts.")
    if result.error:
        click.echo(f"Error: {result.error}")


@main.command()
@click.option("--daily", is_flag=True, help="Generate daily digest")
@click.option("--weekly", is_flag=True, help="Generate weekly digest")
@click.option("--to", default="paul@romatech.com", help="Recipient email address")
def digest(daily: bool, weekly: bool, to: str) -> None:
    """Generate and optionally email intelligence digests."""
    from fertility_sense.agents.digest import DigestGenerator

    pipe = _pipeline()
    dg = DigestGenerator(pipe)

    if weekly:
        click.echo("Generating weekly digest...")
        text = dg.weekly_digest()
        click.echo(text)
        if to:
            click.echo(f"\nSending to {to}...")
            dg.send_digest(digest_type="weekly", to=to)
        return

    # Default to daily
    click.echo("Generating daily digest...")
    text = dg.daily_digest()
    click.echo(text)
    if to:
        click.echo(f"\nSending to {to}...")
        dg.send_digest(digest_type="daily", to=to)


# ------------------------------------------------------------------
# Prospect management
# ------------------------------------------------------------------

@main.group()
def prospects() -> None:
    """Manage prospect database."""


def _prospect_store() -> "ProspectStore":
    from fertility_sense.config import FertilitySenseConfig
    from fertility_sense.outreach.prospect_store import ProspectStore

    cfg = FertilitySenseConfig()
    return ProspectStore(cfg.data_dir / "outreach" / "prospects")


@prospects.command("add")
@click.option("--email", required=True, help="Prospect email")
@click.option("--name", "pname", default="", help="Prospect name")
@click.option("--stage", default="trying", help="Journey stage: pre_ttc, trying, treatment")
@click.option("--diagnosis", default="", help="Diagnosis (pcos, male_factor, unexplained, ...)")
@click.option("--source", default="manual", help="Lead source")
def prospects_add(email: str, pname: str, stage: str, diagnosis: str, source: str) -> None:
    """Add a prospect to the database."""
    from fertility_sense.outreach.prospect_store import Prospect

    store = _prospect_store()
    prospect = Prospect(
        email=email,
        name=pname,
        journey_stage=stage,
        diagnosis=diagnosis,
        source=source,
    )
    store.add(prospect)
    click.echo(f"Added prospect: {email} (stage={stage}, source={source})")


@prospects.command("list")
@click.option("--stage", default=None, help="Filter by journey stage")
def prospects_list(stage: str | None) -> None:
    """List prospects in the database."""
    store = _prospect_store()
    items = store.by_segment(stage) if stage else store.list_all()

    if not items:
        click.echo("No prospects found.")
        return

    click.echo(f"{'Email':<35} {'Name':<20} {'Stage':<12} {'Sequence':<18} {'Score':>6}")
    click.echo("-" * 95)
    for p in items:
        click.echo(
            f"{p.email:<35} {p.name:<20} {p.journey_stage:<12} "
            f"{p.sequence or '-':<18} {p.engagement_score:>6.1f}"
        )
    click.echo(f"\nTotal: {len(items)}")


@prospects.command("import")
@click.option("--csv", "csv_path", required=True, type=click.Path(exists=True), help="CSV file")
def prospects_import(csv_path: str) -> None:
    """Import prospects from a CSV file."""
    from pathlib import Path

    store = _prospect_store()
    count = store.import_csv(Path(csv_path))
    click.echo(f"Imported {count} prospects from {csv_path}")


# ------------------------------------------------------------------
# Sequence management
# ------------------------------------------------------------------

@main.group()
def sequence() -> None:
    """Manage email sequences."""


def _sequence_engine() -> "SequenceEngine":
    from fertility_sense.config import FertilitySenseConfig
    from fertility_sense.outreach.sequences import SequenceEngine

    cfg = FertilitySenseConfig()
    return SequenceEngine(
        sequences_dir=cfg.data_dir / "sequences",
        state_dir=cfg.data_dir / "outreach" / "sequence_state",
    )


@sequence.command("list")
def sequence_list() -> None:
    """List available sequences."""
    engine = _sequence_engine()
    seqs = engine.list_sequences()
    if not seqs:
        click.echo("No sequences loaded.")
        return
    click.echo(f"{'Name':<25} {'Segment':<12} {'Steps':>5}  Description")
    click.echo("-" * 80)
    for s in seqs:
        click.echo(f"{s.name:<25} {s.segment:<12} {len(s.steps):>5}  {s.description}")


@sequence.command("assign")
@click.option("--email", required=True, help="Prospect email")
@click.option("--sequence", "seq_name", required=True, help="Sequence name")
def sequence_assign(email: str, seq_name: str) -> None:
    """Assign a prospect to a sequence."""
    engine = _sequence_engine()
    store = _prospect_store()

    prospect = store.get(email)
    if prospect is None:
        click.echo(f"Prospect not found: {email}. Add first with: prospects add --email {email}")
        return

    try:
        state = engine.assign(email, seq_name)
        store.update(email, sequence=seq_name, sequence_step=0)
        click.echo(f"Assigned {email} to sequence '{seq_name}' (status={state.status})")
    except ValueError as e:
        click.echo(f"Error: {e}")


@sequence.command("run")
@click.option("--dry-run", is_flag=True, help="Preview without advancing state")
def sequence_run(dry_run: bool) -> None:
    """Run due sequence emails."""
    engine = _sequence_engine()
    due = engine.run_due(dry_run=dry_run)

    mode = "DRY RUN" if dry_run else "LIVE"
    click.echo(f"=== Sequence Run ({mode}) — {len(due)} email(s) due ===")

    for item in due:
        click.echo(
            f"  [{item['sequence_name']}] Step {item['step_number']} -> {item['prospect_email']}"
        )
        click.echo(f"    Subject: {item['subject']}")

    if not due:
        click.echo("  No emails due at this time.")


@sequence.command("status")
def sequence_status() -> None:
    """Show sequence enrollment status."""
    engine = _sequence_engine()
    info = engine.status()

    click.echo(f"Sequences loaded: {info['sequences_loaded']}")
    click.echo(f"Total enrolled:   {info['total_enrolled']}")

    if info["by_sequence"]:
        click.echo()
        click.echo(f"{'Sequence':<25} {'Active':>7} {'Done':>7} {'Paused':>7} {'Unsub':>7}")
        click.echo("-" * 60)
        for name, counts in info["by_sequence"].items():
            click.echo(
                f"{name:<25} {counts.get('active', 0):>7} "
                f"{counts.get('completed', 0):>7} {counts.get('paused', 0):>7} "
                f"{counts.get('unsubscribed', 0):>7}"
            )


# ------------------------------------------------------------------
# Content review queue
# ------------------------------------------------------------------

@main.group()
def queue() -> None:
    """Content review queue (HITL)."""


def _queue() -> "ContentQueue":
    """Lazy-create a ContentQueue instance."""
    from pathlib import Path

    from fertility_sense.outreach.content_queue import ContentQueue

    return ContentQueue(Path("data") / "outreach" / "queue")


@queue.command("list")
@click.option("--status", default="pending", help="Filter by status (pending/approved/sent/rejected) or 'all'")
def queue_list(status: str) -> None:
    """List queued content items."""
    q = _queue()
    items = q.list_all(status=None if status == "all" else status)

    if not items:
        click.echo(f"No items with status '{status}'.")
        return

    click.echo(f"{'ID':<10} {'Status':<10} {'Channel':<12} {'Risk':<7} {'Topic':<30} {'Title'}")
    click.echo("-" * 100)
    for item in items:
        title = (item.title[:40] + "...") if len(item.title) > 40 else item.title
        click.echo(
            f"{item.item_id:<10} {item.status:<10} {item.channel:<12} "
            f"{item.risk_tier:<7} {item.topic_id:<30} {title}"
        )

    summary = q.summary()
    click.echo(f"\nSummary: {summary}")


@queue.command("approve")
@click.argument("item_id")
def queue_approve(item_id: str) -> None:
    """Approve a queued content item."""
    q = _queue()
    if q.approve(item_id):
        click.echo(f"Approved: {item_id}")
    else:
        click.echo(f"Item not found: {item_id}")


@queue.command("reject")
@click.argument("item_id")
@click.option("--reason", default="", help="Rejection reason")
def queue_reject(item_id: str, reason: str) -> None:
    """Reject a queued content item."""
    q = _queue()
    if q.reject(item_id, reason=reason):
        click.echo(f"Rejected: {item_id}" + (f" ({reason})" if reason else ""))
    else:
        click.echo(f"Item not found: {item_id}")


@queue.command("send")
@click.argument("item_id")
def queue_send(item_id: str) -> None:
    """Mark an approved item as sent."""
    q = _queue()
    item = q.get(item_id)
    if item is None:
        click.echo(f"Item not found: {item_id}")
        return
    if item.status != "approved":
        click.echo(f"Item must be approved before sending (current: {item.status})")
        return
    q.mark_sent(item_id)
    click.echo(f"Marked sent: {item_id}")


@queue.command("auto-approve")
@click.option("--hours", default=24.0, type=float, help="Max age in hours")
@click.option("--risk-tier", default="green", help="Only auto-approve this risk tier")
def queue_auto_approve(hours: float, risk_tier: str) -> None:
    """Auto-approve stale low-risk items."""
    q = _queue()
    count = q.auto_approve_stale(max_age_hours=hours, risk_tier=risk_tier)
    click.echo(f"Auto-approved {count} item(s) (risk_tier={risk_tier}, age>{hours}h)")


@queue.command("summary")
def queue_summary() -> None:
    """Show queue status summary."""
    q = _queue()
    counts = q.summary()
    if not counts:
        click.echo("Queue is empty.")
        return
    total = sum(counts.values())
    click.echo(f"Queue: {total} total items")
    for status, count in sorted(counts.items()):
        click.echo(f"  {status}: {count}")


# ------------------------------------------------------------------
# Lead magnets
# ------------------------------------------------------------------

@main.group("lead-magnet")
def lead_magnet() -> None:
    """Generate evidence-backed lead magnets."""


def _lead_magnet_gen() -> "LeadMagnetGenerator":
    """Lazy-create a LeadMagnetGenerator."""
    from pathlib import Path

    from fertility_sense.outreach.lead_magnets import LeadMagnetGenerator

    pipe = _pipeline()
    return LeadMagnetGenerator(pipe, Path("data") / "lead_magnets")


@lead_magnet.command("list")
def lead_magnet_list() -> None:
    """List available and generated lead magnets."""
    gen = _lead_magnet_gen()
    available = gen.list_available()
    generated = set(gen.list_generated())

    click.echo(f"{'Name':<25} {'Generated':<12} {'Title'}")
    click.echo("-" * 80)
    for item in available:
        marker = "YES" if item["name"] in generated else "no"
        click.echo(f"{item['name']:<25} {marker:<12} {item['title']}")


@lead_magnet.command("generate")
@click.argument("name")
def lead_magnet_generate(name: str) -> None:
    """Generate a lead magnet by name."""
    gen = _lead_magnet_gen()
    try:
        path = gen.generate(name)
        click.echo(f"Generated: {path}")
    except KeyError as e:
        click.echo(str(e))


if __name__ == "__main__":
    main()
