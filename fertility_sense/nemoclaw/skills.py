"""Domain-specific skill definitions for fertility-sense agents."""

from __future__ import annotations

from fertility_sense.nemoclaw.agents import SkillRef, ClaudeTier

# Consolidated skill registry — all skills across all agents
ALL_SKILLS: list[SkillRef] = [
    # demand-scout skills
    SkillRef("trend-analysis", "Analyze Google Trends for fertility/prenatal keywords, detect velocity changes", ["demand", "trends"]),
    SkillRef("social-scan", "Scan Reddit/forum posts for emerging topics and sentiment", ["demand", "social"]),
    SkillRef("telemetry-parse", "Parse app search/click telemetry into SignalEvent", ["demand", "telemetry"], ClaudeTier.HAIKU),
    SkillRef("signal-normalize", "Normalize raw signals from any source into SignalEvent schema", ["demand", "normalization"], ClaudeTier.HAIKU),

    # evidence-curator skills
    SkillRef("evidence-ingest", "Fetch and parse evidence from a specific feed source into EvidenceRecord", ["evidence", "ingestion"]),
    SkillRef("evidence-grade", "Grade evidence quality using modified GRADE criteria", ["evidence", "grading"]),
    SkillRef("citation-extract", "Extract structured citations from clinical publications", ["evidence", "parsing"], ClaudeTier.HAIKU),
    SkillRef("systematic-review", "Synthesize multiple evidence records for a topic", ["evidence", "synthesis"]),

    # safety-sentinel skills
    SkillRef("alert-monitor", "Poll FDA MedWatch and safety feeds for new alerts", ["safety", "monitoring"], ClaudeTier.HAIKU),
    SkillRef("med-safety-check", "Evaluate medication/supplement against pregnancy safety databases", ["safety", "medication"]),
    SkillRef("exposure-classify", "Classify teratogen exposure risk level", ["safety", "classification"]),
    SkillRef("escalation-trigger", "Determine if safety signal requires immediate escalation", ["safety", "escalation"]),

    # ontology-keeper skills
    SkillRef("topic-classify", "Classify a new topic into the taxonomy", ["ontology", "classification"]),
    SkillRef("alias-resolve", "Resolve multiple surface forms to canonical topic ID", ["ontology", "dedup"], ClaudeTier.HAIKU),
    SkillRef("graph-maintain", "Add/update nodes and edges in the topic graph", ["ontology", "maintenance"], ClaudeTier.SONNET),
    SkillRef("taxonomy-evolve", "Propose taxonomy changes when new topic clusters emerge", ["ontology", "evolution"]),

    # signal-ranker skills
    SkillRef("score-compute", "Compute TOS for a single topic given sub-score inputs", ["scoring", "compute"], ClaudeTier.HAIKU),
    SkillRef("rank-topics", "Rank all scored topics and return top-N", ["scoring", "ranking"], ClaudeTier.HAIKU),
    SkillRef("threshold-filter", "Apply minimum threshold filters per sub-score dimension", ["scoring", "filtering"], ClaudeTier.HAIKU),
    SkillRef("trend-detect", "Detect scoring trend changes (rising, falling, breakout)", ["scoring", "trends"], ClaudeTier.HAIKU),

    # answer-assembler skills
    SkillRef("evidence-retrieve", "Retrieve relevant EvidenceRecords for a topic", ["assembly", "retrieval"], ClaudeTier.HAIKU),
    SkillRef("risk-classify", "Classify topic+query into risk tier", ["assembly", "risk"]),
    SkillRef("template-select", "Select answer template based on risk tier and intent", ["assembly", "template"], ClaudeTier.HAIKU),
    SkillRef("answer-compose", "Compose the final governed answer with inline citations", ["assembly", "composition"]),
    SkillRef("governance-check", "Final governance gate: verify evidence, provenance, disallowed", ["assembly", "governance"]),

    # product-translator skills
    SkillRef("content-brief", "Generate content brief (title, angle, evidence requirements)", ["product", "content"], ClaudeTier.SONNET),
    SkillRef("tool-spec", "Specify interactive tool from demand signals", ["product", "tools"]),
    SkillRef("referral-design", "Design provider/product referral cards with eligibility", ["product", "referral"], ClaudeTier.SONNET),
    SkillRef("commerce-map", "Map commercial opportunities (affiliate, DTC, subscription)", ["product", "commerce"], ClaudeTier.SONNET),
    SkillRef("roadmap-prioritize", "Prioritize product backlog based on TOS rankings", ["product", "strategy"]),

    # ops-monitor skills
    SkillRef("feed-health", "Check each feed's last pull, error rate, record count", ["ops", "feeds"], ClaudeTier.HAIKU),
    SkillRef("freshness-check", "Flag feeds stale beyond expected cadence", ["ops", "freshness"], ClaudeTier.HAIKU),
    SkillRef("pipeline-monitor", "Check pipeline stages for throughput and errors", ["ops", "pipeline"], ClaudeTier.HAIKU),
    SkillRef("alert-dispatch", "Send alerts when thresholds breached", ["ops", "alerting"], ClaudeTier.HAIKU),
]

SKILL_MAP: dict[str, SkillRef] = {s.name: s for s in ALL_SKILLS}
