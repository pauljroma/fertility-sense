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
