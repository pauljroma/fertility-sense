"""Agent configurations for all 8 fertility-sense agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AgentRole(str, Enum):
    EXECUTOR = "executor"
    ANALYST = "analyst"
    PLANNER = "planner"
    ROUTER = "router"


class ClaudeTier(str, Enum):
    HAIKU = "claude-haiku-4-5-20251001"
    SONNET = "claude-sonnet-4-6-20250514"
    OPUS = "claude-opus-4-6-20250514"

    @classmethod
    def resolve(cls, model_id: str) -> str:
        """Return the model_id, applying any fallback mapping for older API keys."""
        return _MODEL_FALLBACKS.get(model_id, model_id)


# Fallback mapping for API keys that don't have access to latest models.
# Set FERTILITY_SENSE_MODEL_FALLBACK=true to use these.
_MODEL_FALLBACKS: dict[str, str] = {}


ROLE_TIER_MAP: dict[AgentRole, ClaudeTier] = {
    AgentRole.EXECUTOR: ClaudeTier.HAIKU,
    AgentRole.ANALYST: ClaudeTier.SONNET,
    AgentRole.PLANNER: ClaudeTier.OPUS,
    AgentRole.ROUTER: ClaudeTier.HAIKU,
}


@dataclass(frozen=True)
class SkillRef:
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    tier_override: ClaudeTier | None = None


@dataclass(frozen=True)
class AgentConfig:
    name: str
    role: AgentRole
    description: str
    skills: list[SkillRef] = field(default_factory=list)
    system_prompt_path: str = ""
    max_tokens: int = 4096
    temperature: float = 0.3
    enabled: bool = True

    @property
    def default_tier(self) -> ClaudeTier:
        return ROLE_TIER_MAP[self.role]


# --- Agent definitions ---

DEMAND_SCOUT = AgentConfig(
    name="demand-scout",
    role=AgentRole.ANALYST,
    description="Monitors search trends, social signals, and app telemetry",
    system_prompt_path="agents/demand-scout.md",
    temperature=0.3,
    skills=[
        SkillRef("trend-analysis", "Analyze Google Trends for fertility keywords", ["demand", "trends"]),
        SkillRef("social-scan", "Scan Reddit/forum posts for emerging topics", ["demand", "social"]),
        SkillRef("telemetry-parse", "Parse app search telemetry", ["demand", "telemetry"], ClaudeTier.HAIKU),
        SkillRef("signal-normalize", "Normalize raw signals to SignalEvent schema", ["demand", "normalization"], ClaudeTier.HAIKU),
    ],
)

EVIDENCE_CURATOR = AgentConfig(
    name="evidence-curator",
    role=AgentRole.ANALYST,
    description="Ingests and grades clinical evidence from CDC, NIH, FDA",
    system_prompt_path="agents/evidence-curator.md",
    max_tokens=8192,
    temperature=0.2,
    skills=[
        SkillRef("evidence-ingest", "Fetch and parse evidence from a feed source", ["evidence", "ingestion"]),
        SkillRef("evidence-grade", "Grade evidence quality using modified GRADE criteria", ["evidence", "grading"]),
        SkillRef("citation-extract", "Extract structured citations from publications", ["evidence", "parsing"], ClaudeTier.HAIKU),
        SkillRef("systematic-review", "Synthesize multiple evidence records for a topic", ["evidence", "synthesis"]),
    ],
)

SAFETY_SENTINEL = AgentConfig(
    name="safety-sentinel",
    role=AgentRole.ANALYST,
    description="Monitors FDA alerts, medication safety, exposure risks",
    system_prompt_path="agents/safety-sentinel.md",
    temperature=0.1,
    skills=[
        SkillRef("alert-monitor", "Poll FDA MedWatch and safety feeds", ["safety", "monitoring"], ClaudeTier.HAIKU),
        SkillRef("med-safety-check", "Evaluate medication against pregnancy safety databases", ["safety", "medication"]),
        SkillRef("exposure-classify", "Classify teratogen exposure risk level", ["safety", "classification"]),
        SkillRef("escalation-trigger", "Determine if safety signal requires immediate escalation", ["safety", "escalation"]),
    ],
)

ONTOLOGY_KEEPER = AgentConfig(
    name="ontology-keeper",
    role=AgentRole.PLANNER,
    description="Maintains topic graph, resolves aliases, classifies topics",
    system_prompt_path="agents/ontology-keeper.md",
    max_tokens=8192,
    temperature=0.2,
    skills=[
        SkillRef("topic-classify", "Classify a new topic into the taxonomy", ["ontology", "classification"]),
        SkillRef("alias-resolve", "Resolve surface forms to canonical topic ID", ["ontology", "dedup"], ClaudeTier.HAIKU),
        SkillRef("graph-maintain", "Add/update nodes and edges in topic graph", ["ontology", "maintenance"], ClaudeTier.SONNET),
        SkillRef("taxonomy-evolve", "Propose taxonomy changes for emerging clusters", ["ontology", "evolution"]),
    ],
)

SIGNAL_RANKER = AgentConfig(
    name="signal-ranker",
    role=AgentRole.EXECUTOR,
    description="Computes composite TOS scores, ranks topics",
    system_prompt_path="agents/signal-ranker.md",
    max_tokens=2048,
    temperature=0.1,
    skills=[
        SkillRef("score-compute", "Compute TOS for a single topic", ["scoring", "compute"]),
        SkillRef("rank-topics", "Rank all scored topics, return top-N", ["scoring", "ranking"]),
        SkillRef("threshold-filter", "Apply minimum threshold filters", ["scoring", "filtering"]),
        SkillRef("trend-detect", "Detect scoring trend changes", ["scoring", "trends"]),
    ],
)

ANSWER_ASSEMBLER = AgentConfig(
    name="answer-assembler",
    role=AgentRole.ANALYST,
    description="Builds governed responses with evidence and provenance",
    system_prompt_path="agents/answer-assembler.md",
    max_tokens=8192,
    temperature=0.2,
    skills=[
        SkillRef("evidence-retrieve", "Retrieve relevant evidence for a topic", ["assembly", "retrieval"], ClaudeTier.HAIKU),
        SkillRef("risk-classify", "Classify topic+query into risk tier", ["assembly", "risk"]),
        SkillRef("template-select", "Select answer template by risk and intent", ["assembly", "template"], ClaudeTier.HAIKU),
        SkillRef("answer-compose", "Compose governed answer with inline citations", ["assembly", "composition"]),
        SkillRef("governance-check", "Final governance gate verification", ["assembly", "governance"]),
    ],
)

PRODUCT_TRANSLATOR = AgentConfig(
    name="product-translator",
    role=AgentRole.PLANNER,
    description="Converts ranked signals into product recommendations",
    system_prompt_path="agents/product-translator.md",
    max_tokens=8192,
    temperature=0.3,
    skills=[
        SkillRef("content-brief", "Generate content brief from demand signals", ["product", "content"], ClaudeTier.SONNET),
        SkillRef("tool-spec", "Specify interactive tool from demand signals", ["product", "tools"]),
        SkillRef("referral-design", "Design provider/product referral cards", ["product", "referral"], ClaudeTier.SONNET),
        SkillRef("commerce-map", "Map commercial opportunities", ["product", "commerce"], ClaudeTier.SONNET),
        SkillRef("roadmap-prioritize", "Prioritize product backlog from TOS", ["product", "strategy"]),
    ],
)

OPS_MONITOR = AgentConfig(
    name="ops-monitor",
    role=AgentRole.EXECUTOR,
    description="Feed health, freshness, pipeline monitoring",
    system_prompt_path="agents/ops-monitor.md",
    max_tokens=2048,
    temperature=0.1,
    skills=[
        SkillRef("feed-health", "Check feed success/error/record counts", ["ops", "feeds"]),
        SkillRef("freshness-check", "Flag stale feeds beyond cadence", ["ops", "freshness"]),
        SkillRef("pipeline-monitor", "Check pipeline throughput and errors", ["ops", "pipeline"]),
        SkillRef("alert-dispatch", "Send alerts to configured channels", ["ops", "alerting"]),
    ],
)

# All agents registry
ALL_AGENTS: list[AgentConfig] = [
    DEMAND_SCOUT,
    EVIDENCE_CURATOR,
    SAFETY_SENTINEL,
    ONTOLOGY_KEEPER,
    SIGNAL_RANKER,
    ANSWER_ASSEMBLER,
    PRODUCT_TRANSLATOR,
    OPS_MONITOR,
]

AGENT_MAP: dict[str, AgentConfig] = {a.name: a for a in ALL_AGENTS}
