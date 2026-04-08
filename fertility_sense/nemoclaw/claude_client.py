"""Anthropic Claude API client with cost tracking and rate limiting."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# Pricing per 1M tokens (input_usd, output_usd)
PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-6": (15.00, 75.00),
    # Aliases / dated variants
    "claude-sonnet-4-6-20250514": (3.00, 15.00),
    "claude-opus-4-6-20250514": (15.00, 75.00),
}


@dataclass
class UsageRecord:
    """Single API call usage record."""

    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime
    agent: str
    skill: str


class BudgetExceededError(Exception):
    """Raised when the cost budget has been exhausted."""


class RateLimitError(Exception):
    """Raised when the per-minute rate limit is hit."""


def _compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute USD cost for a call given token counts."""
    input_price, output_price = PRICING.get(model, (3.00, 15.00))
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


class ClaudeClient:
    """Wrapper around the Anthropic Python SDK with budget and rate-limit guards."""

    def __init__(
        self,
        api_key: str,
        budget_usd: float = 10.0,
        rate_limit_rpm: int = 60,
    ) -> None:
        try:
            import anthropic  # noqa: F811
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required for ClaudeClient. "
                "Install it with: pip install 'anthropic>=0.45'"
            )

        self._client = anthropic.Anthropic(api_key=api_key)
        self._budget_usd = budget_usd
        self._rate_limit_rpm = rate_limit_rpm
        self._total_spend: float = 0.0
        self._usage_log: list[UsageRecord] = []
        # Sliding window of call timestamps for rate limiting
        self._call_times: deque[float] = deque()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call(
        self,
        model: str,
        system: str,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        agent: str = "",
        skill: str = "",
    ) -> tuple[str, UsageRecord]:
        """Send a message to Claude and return (response_text, usage_record).

        Raises:
            BudgetExceededError: if remaining budget is insufficient.
            RateLimitError: if calls-per-minute ceiling is reached.
        """
        self._enforce_rate_limit()
        self._enforce_budget()

        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = _compute_cost(model, input_tokens, output_tokens)

        record = UsageRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            timestamp=datetime.utcnow(),
            agent=agent,
            skill=skill,
        )

        self._total_spend += cost
        self._usage_log.append(record)

        # Extract text from response content blocks
        text_parts: list[str] = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)
        text = "\n".join(text_parts)

        return text, record

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    @property
    def total_spend(self) -> float:
        """Total USD spent so far."""
        return self._total_spend

    @property
    def usage_log(self) -> list[UsageRecord]:
        """Full log of usage records."""
        return list(self._usage_log)

    def budget_remaining(self) -> float:
        """USD remaining before budget is exhausted."""
        return max(0.0, self._budget_usd - self._total_spend)

    # ------------------------------------------------------------------
    # Guards
    # ------------------------------------------------------------------

    def _enforce_budget(self) -> None:
        if self._total_spend >= self._budget_usd:
            raise BudgetExceededError(
                f"Budget exhausted: spent ${self._total_spend:.4f} of ${self._budget_usd:.2f}"
            )

    def _enforce_rate_limit(self) -> None:
        now = time.monotonic()
        # Purge entries older than 60 seconds
        while self._call_times and now - self._call_times[0] > 60:
            self._call_times.popleft()
        if len(self._call_times) >= self._rate_limit_rpm:
            raise RateLimitError(
                f"Rate limit reached: {self._rate_limit_rpm} calls/min"
            )
        self._call_times.append(now)
