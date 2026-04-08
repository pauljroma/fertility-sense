"""Answer assembly pipeline — orchestrates retrieval through governance."""

from __future__ import annotations

import uuid
from datetime import datetime

from fertility_sense.assembly.governor import (
    GovernanceResult,
    build_provenance,
    run_governance_gate,
)
from fertility_sense.assembly.retriever import EvidenceRetriever, RetrievalResult
from fertility_sense.assembly.risk_classifier import classify_risk
from fertility_sense.assembly.template_selector import select_template
from fertility_sense.models.answer import AnswerTemplate, GovernedAnswer
from fertility_sense.models.topic import RiskTier, TopicNode


class AnswerAssembler:
    """Orchestrates the 5-stage answer assembly pipeline.

    Stages:
    1. Retrieve evidence for topic
    2. Classify effective risk tier
    3. Select answer template
    4. Compose sections (placeholder — agent fills in production)
    5. Run governance gate
    """

    def __init__(self, retriever: EvidenceRetriever) -> None:
        self._retriever = retriever

    def assemble(
        self,
        topic: TopicNode,
        query: str,
    ) -> GovernedAnswer:
        """Run the full assembly pipeline for a topic + query."""
        # Stage 1: Retrieve
        retrieval = self._retriever.retrieve(topic.topic_id)

        # Stage 2: Classify risk
        effective_risk = classify_risk(topic, query, retrieval)

        # Stage 3: Select template
        template = select_template(effective_risk, topic.intent)

        # Stage 4: Compose sections
        sections = self._compose_sections(template, retrieval, query)

        # Stage 5: Governance gate
        governance = run_governance_gate(sections, template, retrieval, effective_risk)

        # Build provenance
        provenance = build_provenance(retrieval)

        # Construct governed answer
        answer = GovernedAnswer(
            answer_id=str(uuid.uuid4()),
            topic_id=topic.topic_id,
            query=query,
            template_used=template.template_id,
            risk_tier=effective_risk,
            sections=sections,
            provenance=provenance,
            governance_status=governance.status,
            escalation_reason="; ".join(governance.reasons) if governance.reasons else None,
            generated_at=datetime.utcnow(),
            published_at=datetime.utcnow() if governance.passed else None,
        )

        return answer

    def _compose_sections(
        self,
        template: AnswerTemplate,
        retrieval: RetrievalResult,
        query: str,
    ) -> dict[str, str]:
        """Compose answer sections from template structure.

        In production, this is handled by the answer-assembler agent (Sonnet).
        This implementation provides structured placeholders with evidence citations.
        """
        sections: dict[str, str] = {}

        # Handle BLACK tier escalation
        if template.escalation_text:
            sections["escalation_message"] = template.escalation_text
            return sections

        for section_name in template.structure:
            sections[section_name] = self._compose_section(
                section_name, retrieval, query
            )

        return sections

    def _compose_section(
        self,
        section_name: str,
        retrieval: RetrievalResult,
        query: str,
    ) -> str:
        """Compose a single section. Placeholder for agent-driven composition."""
        if section_name == "sources":
            return self._format_sources(retrieval)

        if section_name in ("important_disclaimer", "consult_provider"):
            return (
                "This information is for educational purposes only and does not "
                "constitute medical advice. Please consult your healthcare provider "
                "for guidance specific to your situation."
            )

        if section_name == "when_to_see_doctor":
            return (
                "Talk to your doctor or midwife if you have questions or concerns "
                "about this topic."
            )

        # Summary/evidence sections: cite available evidence
        if retrieval.evidence:
            findings = []
            for record in retrieval.evidence[:3]:
                if record.key_findings:
                    findings.append(
                        f"{record.key_findings[0]} [{record.source_feed}, "
                        f"{record.publication_date or 'n.d.'}]"
                    )
            if findings:
                return " ".join(findings)

        return f"[Content for '{section_name}' section — requires agent composition]"

    def _format_sources(self, retrieval: RetrievalResult) -> str:
        """Format evidence records as a source list."""
        lines = []
        for r in retrieval.evidence:
            line = f"- {r.title}"
            if r.doi:
                line += f" (DOI: {r.doi})"
            elif r.url:
                line += f" ({r.url})"
            lines.append(line)
        return "\n".join(lines) if lines else "No sources available."
