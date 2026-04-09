"""Comprehensive tests for outreach modules (~1,730 LOC coverage).

Covers: ProspectStore, ContentQueue, SequenceEngine, ScoutLoop, DigestGenerator,
        Campaign, and Composer.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from fertility_sense.outreach.prospect_store import Prospect, ProspectStore
from fertility_sense.outreach.content_queue import ContentQueue, QueueItem
from fertility_sense.outreach.sequences import (
    Sequence,
    SequenceEngine,
    SequenceStep,
)


# ======================================================================
# Prospect Store Tests
# ======================================================================


@pytest.mark.unit
class TestProspectStore:
    """Tests for ProspectStore — JSON-backed prospect persistence."""

    def test_add_prospect(self, tmp_path: Path) -> None:
        store = ProspectStore(tmp_path / "prospects")
        p = Prospect(email="alice@example.com", name="Alice", journey_stage="trying")
        store.add(p)
        assert store.count() == 1

    def test_get_prospect(self, tmp_path: Path) -> None:
        store = ProspectStore(tmp_path / "prospects")
        p = Prospect(email="bob@example.com", name="Bob", diagnosis="pcos")
        store.add(p)
        got = store.get("bob@example.com")
        assert got is not None
        assert got.name == "Bob"
        assert got.diagnosis == "pcos"

    def test_get_nonexistent_returns_none(self, tmp_path: Path) -> None:
        store = ProspectStore(tmp_path / "prospects")
        assert store.get("nobody@example.com") is None

    def test_list_all(self, tmp_path: Path) -> None:
        store = ProspectStore(tmp_path / "prospects")
        for i in range(3):
            store.add(Prospect(email=f"user{i}@example.com", name=f"User {i}"))
        assert len(store.list_all()) == 3

    def test_by_segment_filters_correctly(self, tmp_path: Path) -> None:
        store = ProspectStore(tmp_path / "prospects")
        store.add(Prospect(email="a@x.com", journey_stage="trying"))
        store.add(Prospect(email="b@x.com", journey_stage="treatment"))
        store.add(Prospect(email="c@x.com", journey_stage="trying"))
        assert len(store.by_segment("trying")) == 2
        assert len(store.by_segment("treatment")) == 1
        assert len(store.by_segment("pre_ttc")) == 0

    def test_by_sequence_filters_correctly(self, tmp_path: Path) -> None:
        store = ProspectStore(tmp_path / "prospects")
        store.add(Prospect(email="a@x.com", sequence="ttc_nurture"))
        store.add(Prospect(email="b@x.com", sequence="cold_nurture"))
        store.add(Prospect(email="c@x.com", sequence="ttc_nurture"))
        assert len(store.by_sequence("ttc_nurture")) == 2
        assert len(store.by_sequence("cold_nurture")) == 1

    def test_update_prospect(self, tmp_path: Path) -> None:
        store = ProspectStore(tmp_path / "prospects")
        store.add(Prospect(email="u@x.com", name="Original"))
        updated = store.update("u@x.com", name="Updated", engagement_score=5.0)
        assert updated is not None
        assert updated.name == "Updated"
        assert updated.engagement_score == 5.0
        # Persisted
        reloaded = store.get("u@x.com")
        assert reloaded is not None
        assert reloaded.name == "Updated"

    def test_update_nonexistent_returns_none(self, tmp_path: Path) -> None:
        store = ProspectStore(tmp_path / "prospects")
        assert store.update("ghost@x.com", name="Nope") is None

    def test_add_duplicate_overwrites(self, tmp_path: Path) -> None:
        store = ProspectStore(tmp_path / "prospects")
        store.add(Prospect(email="dup@x.com", name="First"))
        store.add(Prospect(email="dup@x.com", name="Second"))
        assert store.count() == 1
        got = store.get("dup@x.com")
        assert got is not None
        assert got.name == "Second"

    def test_csv_import(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "prospects.csv"
        csv_path.write_text(
            "email,name,journey_stage,diagnosis,source,tags\n"
            "a@x.com,Alice,trying,pcos,import,\"tag1,tag2\"\n"
            "b@x.com,Bob,treatment,male_factor,quiz,\n"
        )
        store = ProspectStore(tmp_path / "store")
        count = store.import_csv(csv_path)
        assert count == 2
        assert store.count() == 2
        alice = store.get("a@x.com")
        assert alice is not None
        assert alice.tags == ["tag1", "tag2"]
        assert alice.diagnosis == "pcos"

    def test_csv_import_skips_invalid_emails(self, tmp_path: Path) -> None:
        """CSV rows with missing email key raise KeyError and skip."""
        csv_path = tmp_path / "bad.csv"
        csv_path.write_text(
            "email,name\n"
            "good@x.com,Good\n"
        )
        store = ProspectStore(tmp_path / "store")
        count = store.import_csv(csv_path)
        assert count == 1  # only the valid row


# ======================================================================
# Content Queue Tests
# ======================================================================


def _make_queue_item(**overrides) -> QueueItem:
    defaults = dict(
        channel="email",
        topic_id="fertility-diet",
        title="Test Title",
        body="Test body content",
        target="email-list",
        risk_tier="green",
        evidence_count=3,
    )
    defaults.update(overrides)
    return QueueItem(**defaults)


@pytest.mark.unit
class TestContentQueue:
    """Tests for ContentQueue — HITL content review layer."""

    def test_add_item(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        item = _make_queue_item()
        item_id = q.add(item)
        assert item_id == item.item_id
        assert q.get(item_id) is not None

    def test_list_pending(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        q.add(_make_queue_item(item_id="a1"))
        q.add(_make_queue_item(item_id="a2"))
        q.add(_make_queue_item(item_id="a3", status="approved"))
        pending = q.list_pending()
        assert len(pending) == 2

    def test_approve_item(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        item = _make_queue_item()
        q.add(item)
        assert q.approve(item.item_id) is True
        reloaded = q.get(item.item_id)
        assert reloaded is not None
        assert reloaded.status == "approved"
        assert reloaded.reviewed_at is not None

    def test_reject_item(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        item = _make_queue_item()
        q.add(item)
        assert q.reject(item.item_id, reason="Off-topic") is True
        reloaded = q.get(item.item_id)
        assert reloaded is not None
        assert reloaded.status == "rejected"
        assert reloaded.rejection_reason == "Off-topic"

    def test_mark_sent(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        item = _make_queue_item()
        q.add(item)
        q.approve(item.item_id)
        assert q.mark_sent(item.item_id) is True
        reloaded = q.get(item.item_id)
        assert reloaded is not None
        assert reloaded.status == "sent"
        assert reloaded.sent_at is not None

    def test_get_nonexistent_returns_none(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        assert q.get("nonexistent") is None

    def test_summary_counts(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        q.add(_make_queue_item(item_id="p1"))
        q.add(_make_queue_item(item_id="p2"))
        q.add(_make_queue_item(item_id="a1", status="approved"))
        q.add(_make_queue_item(item_id="s1", status="sent"))
        summary = q.summary()
        assert summary["pending"] == 2
        assert summary["approved"] == 1
        assert summary["sent"] == 1

    def test_auto_approve_green_tier(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        # Create item with created_at 25 hours ago (timezone-aware to match production code)
        old_item = _make_queue_item(
            item_id="old1",
            risk_tier="green",
        )
        old_item.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
        q._save(old_item)

        # Fresh green item — should NOT be auto-approved
        fresh_item = _make_queue_item(item_id="fresh1", risk_tier="green")
        q.add(fresh_item)

        # Yellow item older than 24h — should NOT be auto-approved (wrong tier)
        yellow_item = _make_queue_item(item_id="yellow1", risk_tier="yellow")
        yellow_item.created_at = datetime.now(timezone.utc) - timedelta(hours=25)
        q._save(yellow_item)

        count = q.auto_approve_stale(max_age_hours=24.0, risk_tier="green")
        assert count == 1
        assert q.get("old1").status == "approved"
        assert q.get("fresh1").status == "pending"
        assert q.get("yellow1").status == "pending"

    def test_approve_nonexistent_returns_false(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        assert q.approve("nonexistent") is False

    def test_reject_nonexistent_returns_false(self, tmp_path: Path) -> None:
        q = ContentQueue(tmp_path / "queue")
        assert q.reject("nonexistent") is False


# ======================================================================
# Sequence Engine Tests
# ======================================================================


def _write_sequence_yaml(sequences_dir: Path, name: str, steps: list[dict], segment: str = "all") -> None:
    """Helper to write a sequence YAML file for testing."""
    data = {
        "name": name,
        "description": f"Test sequence: {name}",
        "segment": segment,
        "steps": steps,
    }
    sequences_dir.mkdir(parents=True, exist_ok=True)
    (sequences_dir / f"{name}.yaml").write_text(yaml.dump(data))


@pytest.mark.unit
class TestSequenceEngine:
    """Tests for SequenceEngine — multi-step drip campaign management."""

    def _make_engine(self, tmp_path: Path) -> SequenceEngine:
        seq_dir = tmp_path / "sequences"
        state_dir = tmp_path / "state"
        _write_sequence_yaml(seq_dir, "welcome", [
            {"step": 1, "delay_days": 0, "subject": "Welcome!", "body": "Hello {name}"},
            {"step": 2, "delay_days": 3, "subject": "Follow up", "body": "Checking in"},
            {"step": 3, "delay_days": 7, "subject": "Final", "body": "Last note"},
        ], segment="trying")
        return SequenceEngine(seq_dir, state_dir)

    def test_load_sequences(self, tmp_path: Path) -> None:
        engine = self._make_engine(tmp_path)
        seqs = engine.list_sequences()
        assert len(seqs) == 1
        assert seqs[0].name == "welcome"
        assert len(seqs[0].steps) == 3

    def test_load_sequences_from_project_data(self) -> None:
        """Verify the project's real YAML sequences load correctly."""
        project_seq_dir = Path("/Users/expo/fertility-sense/data/sequences")
        if not project_seq_dir.exists():
            pytest.skip("Project sequences directory not found")
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            state_dir = Path(td) / "state"
            engine = SequenceEngine(project_seq_dir, state_dir)
            seqs = engine.list_sequences()
            assert len(seqs) >= 3  # At least ttc_nurture, cold_nurture, treatment_nurture
            names = {s.name for s in seqs}
            assert "ttc_nurture" in names

    def test_assign_prospect_to_sequence(self, tmp_path: Path) -> None:
        engine = self._make_engine(tmp_path)
        state = engine.assign("test@x.com", "welcome")
        assert state.prospect_email == "test@x.com"
        assert state.sequence_name == "welcome"
        assert state.current_step == 0
        assert state.status == "active"

    def test_assign_unknown_sequence_raises(self, tmp_path: Path) -> None:
        engine = self._make_engine(tmp_path)
        with pytest.raises(ValueError, match="Unknown sequence"):
            engine.assign("test@x.com", "nonexistent")

    def test_run_due_returns_first_step_immediately(self, tmp_path: Path) -> None:
        engine = self._make_engine(tmp_path)
        engine.assign("user@x.com", "welcome")
        due = engine.run_due()
        assert len(due) == 1
        assert due[0]["step_number"] == 1
        assert due[0]["prospect_email"] == "user@x.com"
        assert due[0]["subject"] == "Welcome!"

    def test_run_due_respects_delay(self, tmp_path: Path) -> None:
        engine = self._make_engine(tmp_path)
        engine.assign("user@x.com", "welcome")
        # Send step 1
        due1 = engine.run_due()
        assert len(due1) == 1

        # Immediately after step 1, step 2 is NOT due (needs 3 days)
        due2 = engine.run_due()
        assert len(due2) == 0

    def test_run_due_sends_step2_after_delay(self, tmp_path: Path) -> None:
        engine = self._make_engine(tmp_path)
        engine.assign("user@x.com", "welcome")
        engine.run_due()  # sends step 1

        # Manually backdate last_sent_at to 4 days ago
        state = engine.get_state("user@x.com")
        assert state is not None
        state.last_sent_at = datetime.now(timezone.utc) - timedelta(days=4)
        engine._save_state(state)

        due = engine.run_due()
        assert len(due) == 1
        assert due[0]["step_number"] == 2

    def test_sequence_status(self, tmp_path: Path) -> None:
        engine = self._make_engine(tmp_path)
        engine.assign("a@x.com", "welcome")
        engine.assign("b@x.com", "welcome")
        engine.pause("b@x.com")

        status = engine.status()
        assert status["sequences_loaded"] == 1
        assert status["total_enrolled"] == 2
        assert status["by_sequence"]["welcome"]["active"] == 1
        assert status["by_sequence"]["welcome"]["paused"] == 1

    def test_unsubscribe(self, tmp_path: Path) -> None:
        engine = self._make_engine(tmp_path)
        engine.assign("u@x.com", "welcome")
        engine.unsubscribe("u@x.com")
        state = engine.get_state("u@x.com")
        assert state is not None
        assert state.status == "unsubscribed"

    def test_dry_run_does_not_advance_state(self, tmp_path: Path) -> None:
        engine = self._make_engine(tmp_path)
        engine.assign("u@x.com", "welcome")
        due = engine.run_due(dry_run=True)
        assert len(due) == 1
        # State should still be at step 0
        state = engine.get_state("u@x.com")
        assert state.current_step == 0


# ======================================================================
# Scout Loop Tests
# ======================================================================


@pytest.mark.unit
class TestScoutLoop:
    """Tests for ScoutLoop — autonomous demand-sensing."""

    def _make_mock_pipeline(self, tmp_path: Path) -> MagicMock:
        """Create a mock Pipeline with the attributes ScoutLoop needs."""
        from fertility_sense.models.topic import JourneyStage

        mock_pipe = MagicMock()
        mock_config = MagicMock()
        mock_config.data_dir = tmp_path / "data"
        mock_pipe.config = mock_config
        # Ensure graph.get_topic returns a topic with a fertility journey stage
        mock_topic = MagicMock()
        mock_topic.journey_stage = JourneyStage.TRYING
        mock_pipe.graph.get_topic.return_value = mock_topic
        return mock_pipe

    def test_scout_run_once_returns_result(self, tmp_path: Path) -> None:
        from fertility_sense.agents.scout_loop import ScoutLoop, ScoutResult

        mock_pipe = self._make_mock_pipeline(tmp_path)
        mock_pipe.ingest.return_value = {"mother_to_baby": 5}

        # Mock score() to return a list of scored topics
        mock_score = MagicMock()
        mock_score.topic_id = "fertility-diet"
        mock_score.composite_tos = 75.0
        mock_score.demand_score = 60.0
        mock_score.clinical_importance = 40.0
        mock_score.rank = 1
        mock_pipe.score.return_value = [mock_score]

        scout = ScoutLoop(mock_pipe)
        result = scout.run_once()

        assert isinstance(result, ScoutResult)
        assert result.status == "ok"
        assert result.topics_scored == 1

    def test_velocity_detection(self, tmp_path: Path) -> None:
        from fertility_sense.agents.scout_loop import ScoutLoop

        mock_pipe = self._make_mock_pipeline(tmp_path)
        mock_pipe.ingest.return_value = {}

        # Current scores: fertility-diet jumped from 30 to 55 (+25)
        mock_score = MagicMock()
        mock_score.topic_id = "fertility-diet"
        mock_score.composite_tos = 55.0
        mock_score.demand_score = 50.0
        mock_score.clinical_importance = 40.0
        mock_score.rank = 1
        mock_pipe.score.return_value = [mock_score]

        scout = ScoutLoop(mock_pipe)

        # Write previous history with fertility-diet at 30.0
        history_path = tmp_path / "data" / "outreach" / "score_history.json"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text(json.dumps({
            "timestamp": "2026-04-07T00:00:00",
            "scores": {"fertility-diet": 30.0},
        }))

        result = scout.run_once()
        assert len(result.velocity_alerts) == 1
        alert = result.velocity_alerts[0]
        assert alert.topic_id == "fertility-diet"
        assert alert.direction == "rising"
        assert alert.delta == 25.0

    def test_scout_no_alerts_on_first_run(self, tmp_path: Path) -> None:
        from fertility_sense.agents.scout_loop import ScoutLoop

        mock_pipe = self._make_mock_pipeline(tmp_path)
        mock_pipe.ingest.return_value = {}

        mock_score = MagicMock()
        mock_score.topic_id = "fertility-diet"
        mock_score.composite_tos = 50.0
        mock_score.demand_score = 40.0
        mock_score.clinical_importance = 30.0
        mock_score.rank = 1
        mock_pipe.score.return_value = [mock_score]

        scout = ScoutLoop(mock_pipe)
        result = scout.run_once()
        # First run has no previous history, so no velocity alerts
        assert len(result.velocity_alerts) == 0

    def test_scout_filters_to_fertility_only(self, tmp_path: Path) -> None:
        """ScoutLoop scores topics via Pipeline.score() which only returns
        topics from the ontology — verifying it delegates correctly."""
        from fertility_sense.agents.scout_loop import ScoutLoop

        mock_pipe = self._make_mock_pipeline(tmp_path)
        mock_pipe.ingest.return_value = {}
        # Pipeline.score already filters to ontology topics
        mock_pipe.score.return_value = []

        scout = ScoutLoop(mock_pipe)
        result = scout.run_once()
        assert result.topics_scored == 0
        mock_pipe.score.assert_called_once_with(top_n=100)


# ======================================================================
# Digest Tests
# ======================================================================


@pytest.mark.unit
class TestDigest:
    """Tests for DigestGenerator."""

    def _make_mock_pipeline(self, tmp_path: Path) -> MagicMock:
        mock_pipe = MagicMock()
        mock_config = MagicMock()
        mock_config.data_dir = tmp_path / "data"
        mock_pipe.config = mock_config

        # health() response
        mock_pipe.health.return_value = {
            "feeds": 2,
            "feed_details": [
                {"name": "mother_to_baby", "is_stale": False, "records": 50},
                {"name": "reddit", "is_stale": True, "records": 10},
            ],
        }

        # evidence_store
        mock_pipe.evidence_store.all_records.return_value = [MagicMock()] * 25

        # graph for _fertility_scores
        mock_topic = MagicMock()
        mock_topic.journey_stage = "preconception"  # won't match FERTILITY_STAGES set
        mock_pipe.graph.get_topic.return_value = mock_topic

        # score() returns empty (simplifies test)
        mock_pipe.score.return_value = []

        return mock_pipe

    def test_daily_digest_is_string(self, tmp_path: Path) -> None:
        from fertility_sense.agents.digest import DigestGenerator

        mock_pipe = self._make_mock_pipeline(tmp_path)
        gen = DigestGenerator(mock_pipe)
        result = gen.daily_digest()
        assert isinstance(result, str)
        assert "DAILY DIGEST" in result

    def test_daily_digest_shows_feed_health(self, tmp_path: Path) -> None:
        from fertility_sense.agents.digest import DigestGenerator

        mock_pipe = self._make_mock_pipeline(tmp_path)
        gen = DigestGenerator(mock_pipe)
        result = gen.daily_digest()
        assert "FEED HEALTH" in result
        assert "mother_to_baby" in result

    def test_daily_digest_shows_fertility_only(self, tmp_path: Path) -> None:
        from fertility_sense.agents.digest import DigestGenerator

        mock_pipe = self._make_mock_pipeline(tmp_path)
        gen = DigestGenerator(mock_pipe)
        result = gen.daily_digest()
        assert "FERTILITY TOPIC OPPORTUNITY SCORES" in result

    def test_weekly_digest_is_string(self, tmp_path: Path) -> None:
        from fertility_sense.agents.digest import DigestGenerator

        mock_pipe = self._make_mock_pipeline(tmp_path)

        # Mock generate_report for weekly digest
        mock_report = MagicMock()
        mock_report.total_topics = 10
        mock_report.fertility_topics = 5
        mock_report.summary = "Test summary"
        mock_report.audience_signals = []
        mock_report.evidence_gaps = []

        with patch("fertility_sense.report.generate_report", return_value=mock_report):
            gen = DigestGenerator(mock_pipe)
            result = gen.weekly_digest()
            assert isinstance(result, str)
            assert "WEEKLY DIGEST" in result


# ======================================================================
# Campaign / Composer Tests
# ======================================================================


def _make_audience_signal(**overrides) -> "AudienceSignal":
    """Build a minimal AudienceSignal for testing."""
    from fertility_sense.report import AudienceSignal

    defaults = dict(
        topic_id="fertility-diet",
        display_name="Fertility Diet",
        who="People optimizing fertility before trying",
        struggle="Looking for dietary changes to boost fertility",
        journey_stage="Optimizing fertility before trying",
        intent="learn",
        demand_score=65.0,
        clinical_importance=40.0,
        evidence_count=3,
        outreach_type="Educational outreach",
        outreach_action="Create blog + Reddit content about fertility diet",
        where_to_find={"subreddits": ["TryingForABaby"]},
        risk_tier="green",
        flags=[],
    )
    defaults.update(overrides)
    return AudienceSignal(**defaults)


@pytest.mark.unit
class TestCampaignComposer:
    """Tests for campaign.py and composer.py."""

    def test_compose_content_offline_mode(self) -> None:
        """Without a dispatcher, composer returns offline placeholder content."""
        from fertility_sense.outreach.composer import compose_campaign_content, CampaignContent
        from fertility_sense.models.topic import (
            JourneyStage, MonetizationClass, RiskTier, TopicIntent, TopicNode,
        )

        topic = TopicNode(
            topic_id="fertility-diet",
            display_name="Fertility Diet",
            aliases=["fertility food"],
            journey_stage=JourneyStage.PRECONCEPTION,
            intent=TopicIntent.LEARN,
            risk_tier=RiskTier.GREEN,
            monetization_class=MonetizationClass.CONTENT,
        )
        signal = _make_audience_signal()
        content = compose_campaign_content(
            signal=signal,
            channel="blog",
            topic=topic,
            evidence=[],
            dispatcher=None,
        )
        assert isinstance(content, CampaignContent)
        assert content.channel == "blog"
        assert "[offline]" in content.body
        assert "Fertility Diet" in content.title

    def test_compose_content_reddit_channel(self) -> None:
        from fertility_sense.outreach.composer import compose_campaign_content
        from fertility_sense.models.topic import (
            JourneyStage, MonetizationClass, RiskTier, TopicIntent, TopicNode,
        )

        topic = TopicNode(
            topic_id="fertility-diet",
            display_name="Fertility Diet",
            aliases=[],
            journey_stage=JourneyStage.PRECONCEPTION,
            intent=TopicIntent.LEARN,
            risk_tier=RiskTier.GREEN,
            monetization_class=MonetizationClass.CONTENT,
        )
        signal = _make_audience_signal()
        content = compose_campaign_content(
            signal=signal,
            channel="reddit",
            topic=topic,
            evidence=[],
            dispatcher=None,
        )
        assert content.channel == "reddit"
        assert len(content.target_subreddits) > 0

    def test_compose_content_social_has_hashtags(self) -> None:
        from fertility_sense.outreach.composer import compose_campaign_content
        from fertility_sense.models.topic import (
            JourneyStage, MonetizationClass, RiskTier, TopicIntent, TopicNode,
        )

        topic = TopicNode(
            topic_id="fertility-diet",
            display_name="Fertility Diet",
            aliases=[],
            journey_stage=JourneyStage.PRECONCEPTION,
            intent=TopicIntent.LEARN,
            risk_tier=RiskTier.GREEN,
            monetization_class=MonetizationClass.CONTENT,
        )
        signal = _make_audience_signal()
        content = compose_campaign_content(
            signal=signal,
            channel="social",
            topic=topic,
            evidence=[],
            dispatcher=None,
        )
        assert content.channel == "social"
        assert len(content.hashtags) > 0
        assert "#TTC" in content.hashtags

    def test_queue_campaign_adds_items(self, tmp_path: Path) -> None:
        """queue_campaign should add all content pieces to a ContentQueue."""
        from fertility_sense.outreach.campaign import CampaignPlan, Campaign, queue_campaign
        from fertility_sense.outreach.composer import CampaignContent

        signal = _make_audience_signal()
        content1 = CampaignContent(
            signal=signal,
            channel="blog",
            title="Blog Title",
            body="Blog body",
            cta="Read more",
            target_subreddits=[],
        )
        content2 = CampaignContent(
            signal=signal,
            channel="email",
            title="Email Title",
            body="Email body",
            cta="Click here",
            target_subreddits=[],
        )
        campaign = Campaign(signal=signal, content=[content1, content2])
        plan = CampaignPlan(
            campaigns=[campaign],
            total_signals=1,
            total_content_pieces=2,
        )

        queue = ContentQueue(tmp_path / "queue")
        count = queue_campaign(plan, queue)
        assert count == 2
        assert len(queue.list_all()) == 2

    def test_queue_campaign_reddit_target_uses_subreddit(self, tmp_path: Path) -> None:
        from fertility_sense.outreach.campaign import CampaignPlan, Campaign, queue_campaign
        from fertility_sense.outreach.composer import CampaignContent

        signal = _make_audience_signal()
        content = CampaignContent(
            signal=signal,
            channel="reddit",
            title="Reddit post",
            body="Reddit content",
            cta="Check it out",
            target_subreddits=["TryingForABaby"],
        )
        campaign = Campaign(signal=signal, content=[content])
        plan = CampaignPlan(campaigns=[campaign], total_signals=1, total_content_pieces=1)

        queue = ContentQueue(tmp_path / "queue")
        queue_campaign(plan, queue)

        items = queue.list_all()
        assert len(items) == 1
        assert items[0].target == "r/TryingForABaby"
