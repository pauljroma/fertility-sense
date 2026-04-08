"""FertilityOrchestrator — domain-specific phased execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PipelinePhase(str, Enum):
    INGEST = "ingest"
    SCORE = "score"
    ASSEMBLE = "assemble"
    TRANSLATE = "translate"


PHASE_AGENTS: dict[PipelinePhase, list[str]] = {
    PipelinePhase.INGEST: ["demand-scout", "evidence-curator", "safety-sentinel"],
    PipelinePhase.SCORE: ["ontology-keeper", "signal-ranker"],
    PipelinePhase.ASSEMBLE: ["answer-assembler"],
    PipelinePhase.TRANSLATE: ["product-translator"],
}


@dataclass
class PhaseResult:
    phase: PipelinePhase
    agents_run: list[str]
    status: str  # "completed", "failed", "escalated"
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


@dataclass
class PipelineRun:
    run_id: str
    phases: list[PhaseResult] = field(default_factory=list)
    status: str = "pending"
    started_at: datetime = field(default_factory=datetime.utcnow)


class FertilityOrchestrator:
    """Orchestrates the full fertility intelligence pipeline.

    Pipeline phases:
    1. INGEST — demand-scout, evidence-curator, safety-sentinel fetch new data
    2. SCORE — ontology-keeper classifies, signal-ranker computes TOS
    3. ASSEMBLE ��� answer-assembler builds governed answers for top topics
    4. TRANSLATE — product-translator converts signals to product decisions

    In production, each phase is backed by actual Claude agent calls.
    This implementation provides the orchestration skeleton.
    """

    def __init__(self) -> None:
        self._runs: list[PipelineRun] = []

    def execute_pipeline(self, run_id: str) -> PipelineRun:
        """Execute the full pipeline sequentially through all phases."""
        run = PipelineRun(run_id=run_id, status="running")
        self._runs.append(run)

        for phase in PipelinePhase:
            result = self._execute_phase(phase)
            run.phases.append(result)

            if result.status == "failed":
                run.status = "failed"
                return run

        run.status = "completed"
        return run

    def execute_phase(self, run_id: str, phase: PipelinePhase) -> PhaseResult:
        """Execute a single pipeline phase."""
        return self._execute_phase(phase)

    def _execute_phase(self, phase: PipelinePhase) -> PhaseResult:
        """Execute a single phase — placeholder for agent-backed execution."""
        agents = PHASE_AGENTS[phase]
        result = PhaseResult(
            phase=phase,
            agents_run=agents,
            status="completed",
        )

        # In production: for each agent in phase, dispatch task via Claude
        # For now, record the phase structure
        for agent_name in agents:
            result.outputs[agent_name] = {
                "status": "completed",
                "message": f"Agent {agent_name} executed for phase {phase.value}",
            }

        result.completed_at = datetime.utcnow()
        return result

    @property
    def last_run(self) -> PipelineRun | None:
        return self._runs[-1] if self._runs else None
