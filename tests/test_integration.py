"""Integration tests for outreach pipeline flows.

These tests use the real Pipeline (with seed data) to verify end-to-end flows
across multiple outreach modules.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from fertility_sense.config import FertilitySenseConfig
from fertility_sense.outreach.content_queue import ContentQueue
from fertility_sense.outreach.prospect_store import Prospect, ProspectStore
from fertility_sense.outreach.sequences import SequenceEngine


@pytest.fixture
def integration_pipeline(tmp_path: Path):
    """Create a real Pipeline rooted in tmp_path but using project data files."""
    project_root = Path("/Users/expo/fertility-sense")
    config = FertilitySenseConfig(
        base_dir=project_root,
        data_dir=tmp_path / "data",
        memory_dir=tmp_path / "data" / "memory",
        evidence_dir=tmp_path / "data" / "evidence",
        feed_state_dir=tmp_path / "data" / "feeds",
        taxonomy_path=project_root / "data" / "ontology" / "taxonomy.yaml",
        aliases_path=project_root / "data" / "ontology" / "aliases.yaml",
    )
    from fertility_sense.pipeline import Pipeline

    pipe = Pipeline(config=config)
    return pipe


@pytest.mark.unit
class TestFullPipelineIngestScoreReport:
    """Integration: Pipeline with seed data can score topics and generate reports."""

    def test_full_pipeline_ingest_score_report(self, integration_pipeline) -> None:
        pipe = integration_pipeline

        # Pipeline loaded seed data — should have topics and evidence
        topics = pipe.graph.all_topics()
        assert len(topics) > 0, "Ontology should have topics"

        # Score all topics
        scores = pipe.score(top_n=10)
        assert len(scores) > 0, "Should produce at least one score"

        # Top score should have reasonable values
        top = scores[0]
        assert top.composite_tos > 0
        assert top.rank == 1

        # Generate report
        from fertility_sense.report import generate_report

        report = generate_report(pipe, top_n=5)
        assert report.total_topics > 0
        assert isinstance(report.summary, str)
        assert len(report.summary) > 10


@pytest.mark.unit
class TestCampaignToQueueFlow:
    """Integration: Generate campaign content and queue it for review."""

    def test_campaign_to_queue_flow(self, integration_pipeline, tmp_path: Path) -> None:
        pipe = integration_pipeline

        # Score topics
        scores = pipe.score(top_n=5)
        assert len(scores) > 0

        # Generate report
        from fertility_sense.report import generate_report

        report = generate_report(pipe, top_n=5)

        # Take the first actionable signal and compose content offline
        actionable = [
            s for s in report.audience_signals
            if "BLOCKED" not in s.flags
        ]
        if not actionable:
            pytest.skip("No actionable signals in seed data")

        signal = actionable[0]
        topic = pipe.graph.get_topic(signal.topic_id)
        assert topic is not None

        from fertility_sense.outreach.composer import compose_campaign_content

        evidence = pipe.evidence_store.by_topic(signal.topic_id)
        content = compose_campaign_content(
            signal=signal,
            channel="blog",
            topic=topic,
            evidence=evidence,
            dispatcher=None,
        )
        assert "[offline]" in content.body

        # Queue it
        from fertility_sense.outreach.content_queue import QueueItem

        queue = ContentQueue(tmp_path / "queue")
        item = QueueItem(
            channel=content.channel,
            topic_id=signal.topic_id,
            title=content.title,
            body=content.body,
            target=signal.topic_id,
            risk_tier=signal.risk_tier,
            evidence_count=signal.evidence_count,
        )
        item_id = queue.add(item)

        # Verify it's in the queue
        pending = queue.list_pending()
        assert len(pending) == 1
        assert pending[0].item_id == item_id

        # Approve and mark sent
        queue.approve(item_id)
        queue.mark_sent(item_id)
        assert queue.get(item_id).status == "sent"


@pytest.mark.unit
class TestProspectSequenceAssignment:
    """Integration: Add prospects, assign to sequences, and run due steps."""

    def test_prospect_sequence_assignment(self, tmp_path: Path) -> None:
        project_root = Path("/Users/expo/fertility-sense")
        seq_dir = project_root / "data" / "sequences"
        if not seq_dir.exists():
            pytest.skip("Sequences directory not found")

        state_dir = tmp_path / "seq_state"
        engine = SequenceEngine(seq_dir, state_dir)

        # Verify sequences loaded
        seqs = engine.list_sequences()
        assert len(seqs) >= 1

        # Pick the first sequence
        seq = seqs[0]

        # Create prospect store and add a prospect
        store = ProspectStore(tmp_path / "prospects")
        prospect = Prospect(
            email="integration@test.com",
            name="Integration Test User",
            journey_stage="trying",
            source="test",
        )
        store.add(prospect)

        # Assign prospect to sequence
        state = engine.assign(prospect.email, seq.name)
        assert state.status == "active"

        # Update prospect record with sequence info
        store.update(prospect.email, sequence=seq.name, sequence_step=0)
        updated = store.get(prospect.email)
        assert updated.sequence == seq.name

        # Run due — first step should fire immediately if delay_days=0
        due = engine.run_due()
        if seq.steps and seq.steps[0].delay_days == 0:
            assert len(due) >= 1
            assert due[0]["prospect_email"] == prospect.email
        else:
            # If first step has a delay, nothing should be due yet
            assert len(due) == 0

        # Verify status
        status = engine.status()
        assert status["total_enrolled"] >= 1
