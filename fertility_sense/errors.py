"""Structured error hierarchy for fertility-sense."""

from __future__ import annotations


class FertilitySenseError(Exception):
    """Base error for all fertility-sense operations."""

    def __init__(self, message: str, code: str, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class FeedIngestionError(FertilitySenseError):
    """Feed failed to ingest data."""

    def __init__(self, feed_name: str, message: str, **kwargs: object):
        super().__init__(
            message,
            code="FEED_INGESTION_ERROR",
            details={"feed": feed_name, **kwargs},
        )


class GovernanceViolationError(FertilitySenseError):
    """Answer failed governance gate."""

    def __init__(self, topic_id: str, violations: list[str], **kwargs: object):
        super().__init__(
            f"Governance violations for {topic_id}",
            code="GOVERNANCE_VIOLATION",
            details={"topic_id": topic_id, "violations": violations, **kwargs},
        )


class AgentDispatchError(FertilitySenseError):
    """Agent failed to execute."""

    def __init__(self, agent_name: str, message: str, **kwargs: object):
        super().__init__(
            message,
            code="AGENT_DISPATCH_ERROR",
            details={"agent": agent_name, **kwargs},
        )


class BudgetExceededError(FertilitySenseError):
    """Claude API budget exceeded."""

    def __init__(self, budget: float, spent: float):
        super().__init__(
            f"Budget ${budget} exceeded (spent ${spent:.4f})",
            code="BUDGET_EXCEEDED",
            details={"budget": budget, "spent": spent},
        )


class ConfigurationError(FertilitySenseError):
    """Configuration is invalid or incomplete."""

    def __init__(self, message: str, **kwargs: object):
        super().__init__(message, code="CONFIGURATION_ERROR", details=kwargs)
