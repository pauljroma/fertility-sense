"""Domain-specific skill definitions for fertility-sense agents."""

from __future__ import annotations

from fertility_sense.nemoclaw.agents import SkillRef, ClaudeTier

# Consolidated skill registry — all skills across all agents
ALL_SKILLS: list[SkillRef] = [
    # demand-scout skills
    SkillRef("trend-analysis", "Analyze LinkedIn, RFP feeds, and broker publications for B2B buying signals", ["demand", "trends"]),
    SkillRef("social-scan", "Scan industry channels for executive moves and benefits announcements", ["demand", "social"]),
    SkillRef("telemetry-parse", "Parse employer benefits survey data and mandate tracking feeds", ["demand", "telemetry"], ClaudeTier.HAIKU),
    SkillRef("signal-normalize", "Normalize raw B2B signals from any source into SignalEvent schema", ["demand", "normalization"], ClaudeTier.HAIKU),

    # evidence-curator skills
    SkillRef("evidence-ingest", "Fetch and parse employer ROI studies, cost benchmarks, and clinical guidelines", ["evidence", "ingestion"]),
    SkillRef("evidence-grade", "Grade evidence quality for sales use using modified GRADE criteria", ["evidence", "grading"]),
    SkillRef("citation-extract", "Extract quotable statistics and citations from publications", ["evidence", "parsing"], ClaudeTier.HAIKU),
    SkillRef("systematic-review", "Synthesize evidence across topics for RFP responses and sales materials", ["evidence", "synthesis"]),

    # safety-sentinel skills
    SkillRef("alert-monitor", "Poll ERISA/DOL updates, state mandate changes, and FDA regulatory feeds", ["safety", "monitoring"], ClaudeTier.HAIKU),
    SkillRef("med-safety-check", "Evaluate regulatory compliance against WIN client contracts", ["safety", "medication"]),
    SkillRef("exposure-classify", "Classify compliance risk level for sales positioning", ["safety", "classification"]),
    SkillRef("escalation-trigger", "Determine if compliance signal requires immediate escalation", ["safety", "escalation"]),

    # ontology-keeper skills
    SkillRef("topic-classify", "Classify a new B2B topic into the enterprise taxonomy", ["ontology", "classification"]),
    SkillRef("alias-resolve", "Resolve surface forms to canonical topic ID across buyer personas", ["ontology", "dedup"], ClaudeTier.HAIKU),
    SkillRef("graph-maintain", "Add/update nodes and edges in the B2B topic graph", ["ontology", "maintenance"], ClaudeTier.SONNET),
    SkillRef("taxonomy-evolve", "Propose taxonomy changes for emerging market segments", ["ontology", "evolution"]),

    # signal-ranker skills
    SkillRef("score-compute", "Compute Deal Opportunity Score for a single prospect", ["scoring", "compute"], ClaudeTier.HAIKU),
    SkillRef("rank-topics", "Rank all scored prospects and return top-N by pipeline value", ["scoring", "ranking"], ClaudeTier.HAIKU),
    SkillRef("threshold-filter", "Apply qualification gates and minimum threshold filters", ["scoring", "filtering"], ClaudeTier.HAIKU),
    SkillRef("trend-detect", "Detect deal score trend changes and velocity shifts", ["scoring", "trends"], ClaudeTier.HAIKU),

    # answer-assembler skills
    SkillRef("evidence-retrieve", "Retrieve relevant evidence for a sales document topic", ["assembly", "retrieval"], ClaudeTier.HAIKU),
    SkillRef("risk-classify", "Classify document type and required evidence grade", ["assembly", "risk"]),
    SkillRef("template-select", "Select document template by buyer persona and sales stage", ["assembly", "template"], ClaudeTier.HAIKU),
    SkillRef("answer-compose", "Compose governed sales document with inline citations", ["assembly", "composition"]),
    SkillRef("governance-check", "Final governance gate: clinical accuracy + brand compliance", ["assembly", "governance"]),

    # product-translator skills
    SkillRef("content-brief", "Generate sales collateral brief from deal opportunity signals", ["product", "content"], ClaudeTier.SONNET),
    SkillRef("tool-spec", "Specify ROI calculator or comparison tool for prospect", ["product", "tools"]),
    SkillRef("referral-design", "Design broker commission proposals and partner materials", ["product", "referral"], ClaudeTier.SONNET),
    SkillRef("commerce-map", "Map revenue opportunities per prospect and buyer persona", ["product", "commerce"], ClaudeTier.SONNET),
    SkillRef("roadmap-prioritize", "Prioritize collateral production based on DOS rankings", ["product", "strategy"]),

    # ops-monitor skills
    SkillRef("feed-health", "Check feed success/error/record counts and deal pipeline health", ["ops", "feeds"], ClaudeTier.HAIKU),
    SkillRef("freshness-check", "Flag stale feeds and stale deals beyond expected cadence", ["ops", "freshness"], ClaudeTier.HAIKU),
    SkillRef("pipeline-monitor", "Check pipeline throughput, conversion metrics, and email sequence performance", ["ops", "pipeline"], ClaudeTier.HAIKU),
    SkillRef("alert-dispatch", "Send alerts on stale deals, degraded feeds, and budget anomalies", ["ops", "alerting"], ClaudeTier.HAIKU),

    # rfp-responder skills
    SkillRef("rfp-parse", "Extract and classify requirements from RFP documents", ["rfp", "parsing"]),
    SkillRef("rfp-score", "Score WIN's fit against each RFP requirement", ["rfp", "scoring"]),
    SkillRef("rfp-draft", "Draft compliant response sections with evidence citations", ["rfp", "drafting"]),
    SkillRef("rfp-review", "Review and validate RFP response for compliance and completeness", ["rfp", "review"]),

    # competitive-intel skills
    SkillRef("competitor-monitor", "Track competitor moves — funding, hires, client wins/losses, pricing", ["competitive", "monitoring"]),
    SkillRef("comparison-doc", "Generate competitor comparison matrices and battle cards", ["competitive", "content"]),
    SkillRef("pricing-analysis", "Analyze and track competitor pricing trends", ["competitive", "pricing"]),
    SkillRef("win-loss-report", "Generate win/loss analysis reports from deal outcomes", ["competitive", "analysis"]),

    # deal-manager skills
    SkillRef("pipeline-check", "Check deal pipeline state and stage distribution", ["deals", "pipeline"], ClaudeTier.HAIKU),
    SkillRef("stage-advance", "Auto-advance deal stages based on triggering events", ["deals", "advancement"], ClaudeTier.HAIKU),
    SkillRef("sequence-trigger", "Trigger email sequences for prospects based on stage and persona", ["deals", "sequences"], ClaudeTier.HAIKU),
    SkillRef("stale-alert", "Detect and alert on stale deals exceeding stage thresholds", ["deals", "alerting"], ClaudeTier.HAIKU),
]

SKILL_MAP: dict[str, SkillRef] = {s.name: s for s in ALL_SKILLS}
