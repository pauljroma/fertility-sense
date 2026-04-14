"""Domain-aware task routing for fertility-sense agents."""

from __future__ import annotations

from fertility_sense.nemoclaw.agents import AGENT_MAP, AgentConfig

# Skill tag → preferred agent mapping
TAG_AGENT_MAP: dict[str, str] = {
    "demand": "demand-scout",
    "trends": "demand-scout",
    "social": "demand-scout",
    "telemetry": "demand-scout",
    "evidence": "evidence-curator",
    "grading": "evidence-curator",
    "ingestion": "evidence-curator",
    "safety": "safety-sentinel",
    "medication": "safety-sentinel",
    "monitoring": "safety-sentinel",
    "ontology": "ontology-keeper",
    "classification": "ontology-keeper",
    "scoring": "signal-ranker",
    "ranking": "signal-ranker",
    "assembly": "answer-assembler",
    "retrieval": "answer-assembler",
    "governance": "answer-assembler",
    "product": "product-translator",
    "content": "product-translator",
    "commerce": "product-translator",
    "ops": "ops-monitor",
    "feeds": "ops-monitor",
    "pipeline": "ops-monitor",
    "alerting": "ops-monitor",
    "rfp": "rfp-responder",
    "parsing": "rfp-responder",
    "drafting": "rfp-responder",
    "review": "rfp-responder",
    "competitive": "competitive-intel",
    "pricing": "competitive-intel",
    "deals": "deal-manager",
    "advancement": "deal-manager",
    "sequences": "deal-manager",
}

# Keyword → agent for natural language routing
KEYWORD_AGENT_MAP: dict[str, str] = {
    "trend": "demand-scout",
    "search": "demand-scout",
    "reddit": "demand-scout",
    "signal": "demand-scout",
    "evidence": "evidence-curator",
    "study": "evidence-curator",
    "publication": "evidence-curator",
    "cdc": "evidence-curator",
    "nih": "evidence-curator",
    "fda": "safety-sentinel",
    "alert": "safety-sentinel",
    "safety": "safety-sentinel",
    "drug": "safety-sentinel",
    "topic": "ontology-keeper",
    "taxonomy": "ontology-keeper",
    "alias": "ontology-keeper",
    "classify": "ontology-keeper",
    "score": "signal-ranker",
    "rank": "signal-ranker",
    "tos": "signal-ranker",
    "answer": "answer-assembler",
    "assemble": "answer-assembler",
    "template": "answer-assembler",
    "product": "product-translator",
    "brief": "product-translator",
    "referral": "product-translator",
    "tool": "product-translator",
    "health": "ops-monitor",
    "status": "ops-monitor",
    "freshness": "ops-monitor",
    "stale": "ops-monitor",
    "rfp": "rfp-responder",
    "proposal": "rfp-responder",
    "competitor": "competitive-intel",
    "progyny": "competitive-intel",
    "carrot": "competitive-intel",
    "maven": "competitive-intel",
    "kindbody": "competitive-intel",
    "battle card": "competitive-intel",
    "deal": "deal-manager",
    "prospect": "deal-manager",
    "pipeline stage": "deal-manager",
}


def route_to_agent(
    prompt: str,
    skill: str | None = None,
    agent: str | None = None,
) -> AgentConfig:
    """Route a task to the appropriate agent.

    Resolution order:
    1. Explicit agent name
    2. Skill tag lookup
    3. Keyword matching in prompt
    4. Default to demand-scout (most common entry point)
    """
    # 1. Explicit agent
    if agent and agent in AGENT_MAP:
        return AGENT_MAP[agent]

    # 2. Skill-based routing
    if skill:
        from fertility_sense.nemoclaw.skills import SKILL_MAP

        skill_ref = SKILL_MAP.get(skill)
        if skill_ref:
            for tag in skill_ref.tags:
                if tag in TAG_AGENT_MAP:
                    agent_name = TAG_AGENT_MAP[tag]
                    if agent_name in AGENT_MAP:
                        return AGENT_MAP[agent_name]

    # 3. Keyword matching
    prompt_lower = prompt.lower()
    for keyword, agent_name in KEYWORD_AGENT_MAP.items():
        if keyword in prompt_lower:
            return AGENT_MAP[agent_name]

    # 4. Default
    return AGENT_MAP["demand-scout"]
