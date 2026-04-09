"""Email sequence engine — manages multi-step drip campaigns.

Sequences are defined as YAML files in ``data/sequences/``.  Prospect
enrollment state is tracked per-email in ``data/outreach/sequence_state/``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Data models
# ------------------------------------------------------------------

@dataclass
class SequenceStep:
    step_number: int
    delay_days: int  # Days after previous step
    subject_template: str
    body_template: str
    segment_filter: str = ""  # Optional journey-stage filter


@dataclass
class Sequence:
    name: str
    description: str
    steps: list[SequenceStep]
    segment: str  # "pre_ttc", "trying", "treatment", "all"


@dataclass
class ProspectSequenceState:
    prospect_email: str
    sequence_name: str
    current_step: int
    started_at: datetime
    last_sent_at: datetime | None = None
    status: str = "active"  # active, completed, paused, unsubscribed


# ------------------------------------------------------------------
# Engine
# ------------------------------------------------------------------

class SequenceEngine:
    """Load YAML sequence definitions and manage prospect enrollment."""

    def __init__(self, sequences_dir: Path, state_dir: Path) -> None:
        self._sequences: dict[str, Sequence] = {}
        self._state_dir = state_dir
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._load_sequences(sequences_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def list_sequences(self) -> list[Sequence]:
        """Return all loaded sequences."""
        return list(self._sequences.values())

    def get_sequence(self, name: str) -> Sequence | None:
        return self._sequences.get(name)

    def assign(self, prospect_email: str, sequence_name: str) -> ProspectSequenceState:
        """Enroll a prospect into a sequence at step 0 (not yet sent)."""
        if sequence_name not in self._sequences:
            raise ValueError(f"Unknown sequence: {sequence_name}")

        state = ProspectSequenceState(
            prospect_email=prospect_email,
            sequence_name=sequence_name,
            current_step=0,
            started_at=datetime.utcnow(),
            status="active",
        )
        self._save_state(state)
        logger.info("Assigned %s to sequence %s", prospect_email, sequence_name)
        return state

    def run_due(self, dry_run: bool = False) -> list[dict]:
        """Find and return all emails that are due to be sent now.

        Each returned dict contains:
            - prospect_email
            - sequence_name
            - step_number
            - subject  (rendered template with raw placeholders)
            - body     (rendered template with raw placeholders)

        When *dry_run* is False the state is advanced after collecting
        due items.  When True, state is left untouched.
        """
        due: list[dict] = []
        now = datetime.utcnow()

        for state in self._load_all_states():
            if state.status != "active":
                continue

            seq = self._sequences.get(state.sequence_name)
            if seq is None:
                continue

            next_step_num = state.current_step + 1
            step = self._get_step(seq, next_step_num)
            if step is None:
                # All steps sent — mark completed
                if not dry_run:
                    state.status = "completed"
                    self._save_state(state)
                continue

            # Calculate when this step is due
            anchor = state.last_sent_at or state.started_at
            due_at = anchor + timedelta(days=step.delay_days)

            if now >= due_at:
                due.append({
                    "prospect_email": state.prospect_email,
                    "sequence_name": state.sequence_name,
                    "step_number": step.step_number,
                    "subject": step.subject_template,
                    "body": step.body_template,
                })
                if not dry_run:
                    state.current_step = next_step_num
                    state.last_sent_at = now
                    self._save_state(state)

        return due

    def get_state(self, prospect_email: str) -> ProspectSequenceState | None:
        """Return enrollment state for a single prospect."""
        path = self._state_path(prospect_email)
        if not path.exists():
            return None
        return self._parse_state(path)

    def pause(self, prospect_email: str) -> None:
        state = self.get_state(prospect_email)
        if state:
            state.status = "paused"
            self._save_state(state)

    def resume(self, prospect_email: str) -> None:
        state = self.get_state(prospect_email)
        if state and state.status == "paused":
            state.status = "active"
            self._save_state(state)

    def unsubscribe(self, prospect_email: str) -> None:
        state = self.get_state(prospect_email)
        if state:
            state.status = "unsubscribed"
            self._save_state(state)

    def status(self) -> dict:
        """Return a summary of all sequences and enrollment counts."""
        states = self._load_all_states()
        by_seq: dict[str, dict[str, int]] = {}
        for s in states:
            bucket = by_seq.setdefault(s.sequence_name, {
                "active": 0, "completed": 0, "paused": 0, "unsubscribed": 0,
            })
            bucket[s.status] = bucket.get(s.status, 0) + 1

        return {
            "sequences_loaded": len(self._sequences),
            "sequence_names": list(self._sequences.keys()),
            "total_enrolled": len(states),
            "by_sequence": by_seq,
        }

    # ------------------------------------------------------------------
    # YAML loading
    # ------------------------------------------------------------------

    def _load_sequences(self, sequences_dir: Path) -> None:
        if not sequences_dir.exists():
            logger.warning("Sequences directory not found: %s", sequences_dir)
            return

        for path in sorted(sequences_dir.glob("*.yaml")):
            try:
                data = yaml.safe_load(path.read_text())
                if data is None:
                    continue
                seq = self._parse_sequence(data)
                self._sequences[seq.name] = seq
                logger.info("Loaded sequence: %s (%d steps)", seq.name, len(seq.steps))
            except Exception:
                logger.exception("Failed to load sequence from %s", path)

    @staticmethod
    def _parse_sequence(data: dict) -> Sequence:
        steps: list[SequenceStep] = []
        for raw in data.get("steps", []):
            steps.append(SequenceStep(
                step_number=raw.get("step", 0),
                delay_days=raw.get("delay_days", 0),
                subject_template=raw.get("subject", ""),
                body_template=raw.get("body", ""),
                segment_filter=raw.get("segment_filter", ""),
            ))
        return Sequence(
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
            segment=data.get("segment", "all"),
        )

    @staticmethod
    def _get_step(seq: Sequence, step_number: int) -> SequenceStep | None:
        for s in seq.steps:
            if s.step_number == step_number:
                return s
        return None

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _state_path(self, email: str) -> Path:
        safe = email.lower().strip().replace("@", "_at_").replace(".", "_")
        return self._state_dir / f"{safe}.json"

    def _save_state(self, state: ProspectSequenceState) -> None:
        path = self._state_path(state.prospect_email)
        data = {
            "prospect_email": state.prospect_email,
            "sequence_name": state.sequence_name,
            "current_step": state.current_step,
            "started_at": state.started_at.isoformat(),
            "last_sent_at": state.last_sent_at.isoformat() if state.last_sent_at else None,
            "status": state.status,
        }
        path.write_text(json.dumps(data, indent=2))

    def _parse_state(self, path: Path) -> ProspectSequenceState:
        data = json.loads(path.read_text())
        return ProspectSequenceState(
            prospect_email=data["prospect_email"],
            sequence_name=data["sequence_name"],
            current_step=data["current_step"],
            started_at=datetime.fromisoformat(data["started_at"]),
            last_sent_at=(
                datetime.fromisoformat(data["last_sent_at"])
                if data.get("last_sent_at")
                else None
            ),
            status=data.get("status", "active"),
        )

    def _load_all_states(self) -> list[ProspectSequenceState]:
        states: list[ProspectSequenceState] = []
        for p in self._state_dir.glob("*.json"):
            try:
                states.append(self._parse_state(p))
            except Exception:
                logger.warning("Skipping corrupt state file: %s", p)
        return states
