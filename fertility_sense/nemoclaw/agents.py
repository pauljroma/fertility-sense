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
    SONNET = "claude-sonnet-4-6"
    OPUS = "claude-opus-4-6"

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
    description="Monitors B2B demand signals — executive moves, RFPs, broker activity, mandate changes",
    system_prompt_path="agents/demand-scout.md",
    temperature=0.3,
    skills=[
        SkillRef("trend-analysis", "Analyze LinkedIn, RFP feeds, and broker publications for buying signals", ["demand", "trends"]),
        SkillRef("social-scan", "Scan industry channels for executive moves and benefits announcements", ["demand", "social"]),
        SkillRef("telemetry-parse", "Parse employer benefits survey data and mandate tracking feeds", ["demand", "telemetry"], ClaudeTier.HAIKU),
        SkillRef("signal-normalize", "Normalize raw B2B signals to SignalEvent schema", ["demand", "normalization"], ClaudeTier.HAIKU),
    ],
)

EVIDENCE_CURATOR = AgentConfig(
    name="evidence-curator",
    role=AgentRole.ANALYST,
    description="Curates WIN's evidence arsenal — ROI studies, cost benchmarks, outcomes data, competitive pricing",
    system_prompt_path="agents/evidence-curator.md",
    max_tokens=8192,
    temperature=0.2,
    skills=[
        SkillRef("evidence-ingest", "Fetch and parse employer ROI studies, cost benchmarks, and clinical guidelines", ["evidence", "ingestion"]),
        SkillRef("evidence-grade", "Grade evidence quality for sales use using modified GRADE criteria", ["evidence", "grading"]),
        SkillRef("citation-extract", "Extract quotable statistics and citations from publications", ["evidence", "parsing"], ClaudeTier.HAIKU),
        SkillRef("systematic-review", "Synthesize evidence across topics for RFP responses and sales materials", ["evidence", "synthesis"]),
    ],
)

SAFETY_SENTINEL = AgentConfig(
    name="safety-sentinel",
    role=AgentRole.ANALYST,
    description="Monitors compliance risks — ERISA changes, state mandates, regulatory enforcement, brand risk",
    system_prompt_path="agents/safety-sentinel.md",
    temperature=0.1,
    skills=[
        SkillRef("alert-monitor", "Poll ERISA/DOL updates, state mandate changes, and FDA regulatory feeds", ["safety", "monitoring"], ClaudeTier.HAIKU),
        SkillRef("med-safety-check", "Evaluate regulatory compliance against WIN client contracts", ["safety", "medication"]),
        SkillRef("exposure-classify", "Classify compliance risk level for sales positioning", ["safety", "classification"]),
        SkillRef("escalation-trigger", "Determine if compliance signal requires immediate escalation", ["safety", "escalation"]),
    ],
)

ONTOLOGY_KEEPER = AgentConfig(
    name="ontology-keeper",
    role=AgentRole.PLANNER,
    description="Maintains B2B topic taxonomy — benefit categories, cost drivers, buyer pain points, competitive themes",
    system_prompt_path="agents/ontology-keeper.md",
    max_tokens=8192,
    temperature=0.2,
    skills=[
        SkillRef("topic-classify", "Classify a new B2B topic into the enterprise taxonomy", ["ontology", "classification"]),
        SkillRef("alias-resolve", "Resolve surface forms to canonical topic ID across buyer personas", ["ontology", "dedup"], ClaudeTier.HAIKU),
        SkillRef("graph-maintain", "Add/update nodes and edges in the B2B topic graph", ["ontology", "maintenance"], ClaudeTier.SONNET),
        SkillRef("taxonomy-evolve", "Propose taxonomy changes for emerging market segments", ["ontology", "evolution"]),
    ],
)

SIGNAL_RANKER = AgentConfig(
    name="signal-ranker",
    role=AgentRole.EXECUTOR,
    description="Computes Deal Opportunity Scores, ranks prospects and topics by pipeline value",
    system_prompt_path="agents/signal-ranker.md",
    max_tokens=2048,
    temperature=0.1,
    skills=[
        SkillRef("score-compute", "Compute Deal Opportunity Score for a single prospect", ["scoring", "compute"]),
        SkillRef("rank-topics", "Rank all scored prospects, return top-N by pipeline value", ["scoring", "ranking"]),
        SkillRef("threshold-filter", "Apply qualification gates and minimum threshold filters", ["scoring", "filtering"]),
        SkillRef("trend-detect", "Detect deal score trend changes and velocity shifts", ["scoring", "trends"]),
    ],
)

ANSWER_ASSEMBLER = AgentConfig(
    name="answer-assembler",
    role=AgentRole.ANALYST,
    description="Assembles governed B2B sales documents — executive briefs, RFP sections, case studies, broker materials",
    system_prompt_path="agents/answer-assembler.md",
    max_tokens=8192,
    temperature=0.2,
    skills=[
        SkillRef("evidence-retrieve", "Retrieve relevant evidence for a sales document topic", ["assembly", "retrieval"], ClaudeTier.HAIKU),
        SkillRef("risk-classify", "Classify document type and required evidence grade", ["assembly", "risk"]),
        SkillRef("template-select", "Select document template by buyer persona and sales stage", ["assembly", "template"], ClaudeTier.HAIKU),
        SkillRef("answer-compose", "Compose governed sales document with inline citations", ["assembly", "composition"]),
        SkillRef("governance-check", "Final governance gate: clinical accuracy + brand compliance", ["assembly", "governance"]),
    ],
)

PRODUCT_TRANSLATOR = AgentConfig(
    name="product-translator",
    role=AgentRole.PLANNER,
    description="Converts pipeline intelligence into sales collateral — case studies, ROI models, RFP drafts, broker proposals",
    system_prompt_path="agents/product-translator.md",
    max_tokens=8192,
    temperature=0.3,
    skills=[
        SkillRef("content-brief", "Generate sales collateral brief from deal opportunity signals", ["product", "content"], ClaudeTier.SONNET),
        SkillRef("tool-spec", "Specify ROI calculator or comparison tool for prospect", ["product", "tools"]),
        SkillRef("referral-design", "Design broker commission proposals and partner materials", ["product", "referral"], ClaudeTier.SONNET),
        SkillRef("commerce-map", "Map revenue opportunities per prospect and buyer persona", ["product", "commerce"], ClaudeTier.SONNET),
        SkillRef("roadmap-prioritize", "Prioritize collateral production based on DOS rankings", ["product", "strategy"]),
    ],
)

OPS_MONITOR = AgentConfig(
    name="ops-monitor",
    role=AgentRole.EXECUTOR,
    description="Monitors growth engine health — deal pipeline, email sequences, conversion metrics, feed freshness",
    system_prompt_path="agents/ops-monitor.md",
    max_tokens=2048,
    temperature=0.1,
    skills=[
        SkillRef("feed-health", "Check feed success/error/record counts and deal pipeline health", ["ops", "feeds"]),
        SkillRef("freshness-check", "Flag stale feeds and stale deals beyond expected cadence", ["ops", "freshness"]),
        SkillRef("pipeline-monitor", "Check pipeline throughput, conversion metrics, and email sequence performance", ["ops", "pipeline"]),
        SkillRef("alert-dispatch", "Send alerts on stale deals, degraded feeds, and budget anomalies", ["ops", "alerting"]),
    ],
)


RFP_RESPONDER = AgentConfig(
    name="rfp-responder",
    role=AgentRole.ANALYST,
    description="Parses RFP requirements, scores WIN's fit, generates draft RFP response sections with evidence",
    system_prompt_path="agents/rfp-responder.md",
    max_tokens=8192,
    temperature=0.2,
    skills=[
        SkillRef("rfp-parse", "Extract and classify requirements from RFP documents", ["rfp", "parsing"]),
        SkillRef("rfp-score", "Score WIN's fit against each RFP requirement", ["rfp", "scoring"]),
        SkillRef("rfp-draft", "Draft compliant response sections with evidence citations", ["rfp", "drafting"]),
        SkillRef("rfp-review", "Review and validate RFP response for compliance and completeness", ["rfp", "review"]),
    ],
)

COMPETITIVE_INTEL = AgentConfig(
    name="competitive-intel",
    role=AgentRole.ANALYST,
    description="Monitors Progyny, Carrot, Maven, Kindbody — generates competitive positioning for WIN's sales team",
    system_prompt_path="agents/competitive-intel.md",
    max_tokens=8192,
    temperature=0.3,
    skills=[
        SkillRef("competitor-monitor", "Track competitor moves — funding, hires, client wins/losses, pricing", ["competitive", "monitoring"]),
        SkillRef("comparison-doc", "Generate competitor comparison matrices and battle cards", ["competitive", "content"]),
        SkillRef("pricing-analysis", "Analyze and track competitor pricing trends", ["competitive", "pricing"]),
        SkillRef("win-loss-report", "Generate win/loss analysis reports from deal outcomes", ["competitive", "analysis"]),
    ],
)

DEAL_MANAGER = AgentConfig(
    name="deal-manager",
    role=AgentRole.EXECUTOR,
    description="Tracks deal pipeline, auto-advances stages, triggers sequences, alerts on stale deals",
    system_prompt_path="agents/deal-manager.md",
    max_tokens=2048,
    temperature=0.1,
    skills=[
        SkillRef("pipeline-check", "Check deal pipeline state and stage distribution", ["deals", "pipeline"]),
        SkillRef("stage-advance", "Auto-advance deal stages based on triggering events", ["deals", "advancement"]),
        SkillRef("sequence-trigger", "Trigger email sequences for prospects based on stage and persona", ["deals", "sequences"]),
        SkillRef("stale-alert", "Detect and alert on stale deals exceeding stage thresholds", ["deals", "alerting"]),
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
    RFP_RESPONDER,
    COMPETITIVE_INTEL,
    DEAL_MANAGER,
]

AGENT_MAP: dict[str, AgentConfig] = {a.name: a for a in ALL_AGENTS}
