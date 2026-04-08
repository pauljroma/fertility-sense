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


@main.command()
@click.option("--feed", default="all", help="Feed name or 'all'")
def ingest(feed: str) -> None:
    """Trigger feed ingestion."""
    click.echo(f"Ingesting feed: {feed}")
    # In production: instantiate FeedRegistry and run feeds
    click.echo("Feed ingestion complete.")


@main.command()
@click.option("--topic", default="all", help="Topic ID or 'all'")
@click.option("--top", default=20, type=int, help="Show top N topics")
def score(topic: str, top: int) -> None:
    """Compute Topic Opportunity Scores."""
    click.echo(f"Scoring topics: {topic} (showing top {top})")
    # In production: load ontology, compute scores, rank
    click.echo("Scoring complete.")


@main.command()
@click.option("--topic", required=True, help="Topic ID")
@click.option("--query", required=True, help="User query")
def answer(topic: str, query: str) -> None:
    """Assemble a governed answer."""
    click.echo(f"Assembling answer for topic={topic}, query='{query}'")
    # In production: run full assembly pipeline
    click.echo("Answer assembly complete.")


@main.command()
@click.option("--all", "show_all", is_flag=True, help="Show all status")
@click.option("--feeds", is_flag=True, help="Show feed status")
@click.option("--agents", is_flag=True, help="Show agent status")
def status(show_all: bool, feeds: bool, agents: bool) -> None:
    """Show pipeline health status."""
    if show_all or feeds:
        click.echo("=== Feed Health ===")
        click.echo("(No feeds configured yet)")

    if show_all or agents:
        click.echo("=== Agent Status ===")
        from fertility_sense.nemoclaw.agents import ALL_AGENTS

        for agent in ALL_AGENTS:
            tier = agent.default_tier.value.split("-")[1]  # haiku/sonnet/opus
            click.echo(f"  {agent.name:<25} {agent.role.value:<10} {tier}")

    if not (show_all or feeds or agents):
        click.echo("Use --all, --feeds, or --agents")


@main.command()
def pipeline() -> None:
    """Run the full intelligence pipeline."""
    from fertility_sense.nemoclaw.orchestrator import FertilityOrchestrator

    orch = FertilityOrchestrator()
    run_id = str(uuid.uuid4())[:8]
    click.echo(f"Running pipeline (run_id={run_id})...")
    result = orch.execute_pipeline(run_id)
    click.echo(f"Pipeline {result.status}:")
    for phase in result.phases:
        click.echo(f"  {phase.phase.value}: {phase.status} ({', '.join(phase.agents_run)})")


if __name__ == "__main__":
    main()
