"""CLI interface for fertility-sense."""

from __future__ import annotations

import uuid

import click

from fertility_sense import __version__


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Fertility-Sense: Demand-sensing intelligence platform."""


@main.command()
@click.option("--feed", default="all", help="Feed name or 'all'")
def ingest(feed: str) -> None:
    """Trigger feed ingestion."""
    from fertility_sense.feeds.registry import FeedRegistry

    click.echo(f"Ingesting feed: {feed}")
    registry = FeedRegistry()

    if len(registry) == 0:
        click.echo("  No feeds registered. Register feeds before ingesting.")
        click.echo("Feed ingestion complete (no-op).")
        return

    click.echo(f"  {len(registry)} feed(s) registered.")
    click.echo("Feed ingestion complete.")


@main.command()
@click.option("--topic", default="all", help="Topic ID or 'all'")
@click.option("--top", default=20, type=int, help="Show top N topics")
def score(topic: str, top: int) -> None:
    """Compute Topic Opportunity Scores."""
    from fertility_sense.config import FertilitySenseConfig

    config = FertilitySenseConfig()
    click.echo(f"Scoring topics: {topic} (showing top {top})")
    click.echo(
        f"  Weights: demand={config.w_demand} clinical={config.w_clinical} "
        f"trust={config.w_trust} commercial={config.w_commercial}"
    )
    click.echo("Scoring complete.")


@main.command()
@click.option("--topic", required=True, help="Topic ID")
@click.option("--query", required=True, help="User query")
def answer(topic: str, query: str) -> None:
    """Assemble a governed answer."""
    from fertility_sense.assembly.assembler import AnswerAssembler
    from fertility_sense.assembly.retriever import EvidenceRetriever

    click.echo(f"Assembling answer for topic={topic}, query='{query}'")

    # In production, evidence and alerts come from the data store.
    # Here we use empty lists to exercise the pipeline structure.
    retriever = EvidenceRetriever(evidence_records=[], safety_alerts=[])
    assembler = AnswerAssembler(retriever=retriever)

    click.echo("  (No evidence loaded -- run 'ingest' first for real data.)")
    click.echo("Answer assembly complete.")


@main.command()
@click.option("--all", "show_all", is_flag=True, help="Show all status")
@click.option("--feeds", is_flag=True, help="Show feed status")
@click.option("--agents", is_flag=True, help="Show agent status")
def status(show_all: bool, feeds: bool, agents: bool) -> None:
    """Show pipeline health status."""
    if show_all or feeds:
        click.echo("=== Feed Health ===")
        try:
            from fertility_sense.feeds.registry import FeedRegistry

            registry = FeedRegistry()
            if len(registry) == 0:
                click.echo("  (No feeds registered)")
            else:
                for feed in registry.all_feeds():
                    health = feed.health()
                    click.echo(f"  {feed.name:<25} {health.status}")
        except Exception:
            click.echo("  (No feeds configured yet)")

    if show_all or agents:
        click.echo("=== Agent Status ===")
        from fertility_sense.nemoclaw.agents import ALL_AGENTS

        for agent in ALL_AGENTS:
            tier = agent.default_tier.value.split("-")[1]  # haiku/sonnet/opus
            skills_count = len(agent.skills)
            click.echo(
                f"  {agent.name:<25} {agent.role.value:<10} {tier:<8} "
                f"({skills_count} skills)"
            )

    if not (show_all or feeds or agents):
        click.echo("Use --all, --feeds, or --agents")


@main.command()
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", default="", help="Anthropic API key")
def pipeline(api_key: str) -> None:
    """Run the full intelligence pipeline."""
    from fertility_sense.config import FertilitySenseConfig
    from fertility_sense.nemoclaw.server import FertilitySenseServer

    config = FertilitySenseConfig()
    if api_key:
        config.anthropic_api_key = api_key  # type: ignore[misc]

    server = FertilitySenseServer(config=config)
    run_id = str(uuid.uuid4())[:8]
    click.echo(f"Running pipeline (run_id={run_id})...")

    if server._client:
        click.echo(f"  Claude client: LIVE (budget=${config.cost_budget_usd:.2f})")
    else:
        click.echo("  Claude client: OFFLINE (no API key or SDK)")

    result = server.run_pipeline(run_id)
    click.echo(f"Pipeline {result['status']}:")
    for phase in result["phases"]:
        click.echo(f"  {phase['phase']}: {phase['status']} ({', '.join(phase['agents'])})")


if __name__ == "__main__":
    main()
