"""FertilityOrchestrator — domain-specific phased execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fertility_sense.nemoclaw.dispatcher import AgentDispatcher


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

    def __init__(self, dispatcher: AgentDispatcher | None = None) -> None:
        self._runs: list[PipelineRun] = []
        self._dispatcher = dispatcher

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
        """Execute a single phase.

        When a dispatcher is available, each agent in the phase is called via
        Claude.  Otherwise falls back to the original stub behaviour so that
        existing tests continue to pass.
        """
        agents = PHASE_AGENTS[phase]
        result = PhaseResult(
            phase=phase,
            agents_run=agents,
            status="completed",
        )

        if self._dispatcher is None:
            # Stub mode — no dispatcher attached
            for agent_name in agents:
                result.outputs[agent_name] = {
                    "status": "completed",
                    "message": f"Agent {agent_name} executed for phase {phase.value}",
                }
        else:
            # Dispatcher mode — call each agent
            for agent_name in agents:
                prompt = f"Execute {phase.value} phase tasks."
                dispatch_result = self._dispatcher.dispatch(
                    agent_name=agent_name,
                    prompt=prompt,
                )
                result.outputs[agent_name] = {
                    "status": dispatch_result.status,
                    "model": dispatch_result.model_used,
                    "output": dispatch_result.output[:500],
                    "error": dispatch_result.error,
                }
                if dispatch_result.status == "failed":
                    result.errors.append(
                        f"{agent_name}: {dispatch_result.error}"
                    )

            # Mark phase failed if any agent failed hard
            if result.errors:
                result.status = "failed"

        result.completed_at = datetime.utcnow()
        return result

    @property
    def last_run(self) -> PipelineRun | None:
        return self._runs[-1] if self._runs else None
