"""Tests for Workstream 5: observability, errors, and governance enrichment."""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from fertility_sense.errors import (
    AgentDispatchError,
    BudgetExceededError,
    ConfigurationError,
    FeedIngestionError,
    FertilitySenseError,
    GovernanceViolationError,
)

# ---------------------------------------------------------------------------
# 1. Error hierarchy
# ---------------------------------------------------------------------------


class TestErrorHierarchy:
    """All domain errors inherit from FertilitySenseError."""

    @pytest.mark.smoke
    @pytest.mark.parametrize(
        "exc_cls",
        [
            FeedIngestionError,
            GovernanceViolationError,
            AgentDispatchError,
            BudgetExceededError,
            ConfigurationError,
        ],
    )
    def test_inherits_from_base(self, exc_cls: type) -> None:
        assert issubclass(exc_cls, FertilitySenseError)
        assert issubclass(exc_cls, Exception)

    @pytest.mark.unit
    def test_feed_ingestion_error_fields(self) -> None:
        err = FeedIngestionError("google_trends", "timeout after 30s", attempt=3)
        assert err.code == "FEED_INGESTION_ERROR"
        assert err.details["feed"] == "google_trends"
        assert err.details["attempt"] == 3
        assert "timeout" in err.message

    @pytest.mark.unit
    def test_governance_violation_error_fields(self) -> None:
        err = GovernanceViolationError("topic_123", ["diagnosis", "dosage"])
        assert err.code == "GOVERNANCE_VIOLATION"
        assert err.details["topic_id"] == "topic_123"
        assert err.details["violations"] == ["diagnosis", "dosage"]

    @pytest.mark.unit
    def test_budget_exceeded_error_fields(self) -> None:
        err = BudgetExceededError(budget=5.0, spent=5.1234)
        assert err.code == "BUDGET_EXCEEDED"
        assert err.details["budget"] == 5.0
        assert err.details["spent"] == 5.1234
        assert "$5.0" in err.message

    @pytest.mark.unit
    def test_configuration_error_fields(self) -> None:
        err = ConfigurationError("missing API key", key="ANTHROPIC_API_KEY")
        assert err.code == "CONFIGURATION_ERROR"
        assert err.details["key"] == "ANTHROPIC_API_KEY"

    @pytest.mark.unit
    def test_agent_dispatch_error_fields(self) -> None:
        err = AgentDispatchError("scorer", "model overloaded", retry=True)
        assert err.code == "AGENT_DISPATCH_ERROR"
        assert err.details["agent"] == "scorer"
        assert err.details["retry"] is True


# ---------------------------------------------------------------------------
# 2. Structured logging
# ---------------------------------------------------------------------------


class TestStructuredLogging:
    @pytest.mark.unit
    def test_setup_returns_bound_logger(self) -> None:
        from fertility_sense.log import setup_logging

        logger = setup_logging(level="DEBUG", json_output=True)
        # structlog BoundLogger should have standard methods
        assert callable(getattr(logger, "info", None))
        assert callable(getattr(logger, "error", None))
        assert callable(getattr(logger, "warning", None))

    @pytest.mark.unit
    def test_json_output_format(self, capsys: pytest.CaptureFixture[str]) -> None:
        from fertility_sense.log import setup_logging

        logger = setup_logging(level="DEBUG", json_output=True)
        logger.info("test_event", key="value")

        captured = capsys.readouterr()
        # JSON goes to stderr
        line = captured.err.strip().split("\n")[-1]
        data = json.loads(line)
        assert data["event"] == "test_event"
        assert data["key"] == "value"
        assert "timestamp" in data

    @pytest.mark.unit
    def test_context_vars(self, capsys: pytest.CaptureFixture[str]) -> None:
        from fertility_sense.log import request_id_var, setup_logging

        logger = setup_logging(level="DEBUG", json_output=True)
        token = request_id_var.set("req-abc-123")
        try:
            logger.info("with_context")
            captured = capsys.readouterr()
            line = captured.err.strip().split("\n")[-1]
            data = json.loads(line)
            assert data.get("request_id") == "req-abc-123"
        finally:
            request_id_var.reset(token)


# ---------------------------------------------------------------------------
# 3. Disallowed patterns — YAML loading and enriched patterns
# ---------------------------------------------------------------------------

_YAML_PATH = Path(__file__).resolve().parents[1] / "data" / "governance" / "disallowed_patterns.yaml"


class TestDisallowedPatterns:
    @pytest.mark.unit
    def test_yaml_file_exists(self) -> None:
        assert _YAML_PATH.exists(), f"Expected YAML at {_YAML_PATH}"

    @pytest.mark.unit
    def test_yaml_parses(self) -> None:
        data = yaml.safe_load(_YAML_PATH.read_text())
        assert "disallowed_classes" in data
        assert len(data["disallowed_classes"]) >= 7  # 5 original + 2 new

    @pytest.mark.unit
    def test_load_from_yaml(self) -> None:
        from fertility_sense.governance.disallowed import _load_from_yaml

        classes = _load_from_yaml(_YAML_PATH)
        names = {c.name for c in classes}
        assert "diagnosis" in names
        assert "false_equivalence" in names
        assert "unproven_claims" in names

    @pytest.mark.unit
    def test_fallback_when_yaml_missing(self) -> None:
        from fertility_sense.governance.disallowed import _load_classes

        classes = _load_classes(Path("/nonexistent/path.yaml"))
        assert len(classes) >= 7

    @pytest.mark.unit
    def test_reload_patterns(self) -> None:
        from fertility_sense.governance.disallowed import reload_patterns

        count = reload_patterns(_YAML_PATH)
        assert count >= 7

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "text,expected_class",
        [
            # Original patterns
            ("you have PCOS", "diagnosis"),
            ("take 200mg of progesterone", "dosage"),
            ("this is not an emergency", "emergency_triage"),
            ("you will definitely conceive", "outcome_guarantee"),
            ("you don't need a doctor", "anti_medical"),
            # Enriched patterns
            ("you likely have endometriosis", "diagnosis"),
            ("this indicates you have fibroids", "diagnosis"),
            ("the recommended amount is 500", "dosage"),
            ("the optimal dose for fertility", "dosage"),
            ("doctors just want to prescribe", "anti_medical"),
            ("natural is better than IVF", "anti_medical"),
            # New classes
            ("acupuncture is just as good as IVF", "false_equivalence"),
            ("equivalent to medication for PCOS", "false_equivalence"),
            ("clinically proven to boost fertility", "unproven_claims"),
            ("scientifically shown that supplements work", "unproven_claims"),
        ],
    )
    def test_pattern_matches(self, text: str, expected_class: str) -> None:
        from fertility_sense.governance.disallowed import check_disallowed

        violations = check_disallowed(text)
        matched_classes = [v[0] for v in violations]
        assert expected_class in matched_classes, (
            f"Expected '{expected_class}' to match '{text}', got {matched_classes}"
        )


# ---------------------------------------------------------------------------
# 4. Metrics module
# ---------------------------------------------------------------------------


class TestMetrics:
    @pytest.mark.unit
    def test_get_metrics_response_returns_bytes(self) -> None:
        from fertility_sense.metrics import get_metrics_response

        result = get_metrics_response()
        assert isinstance(result, bytes)

    @pytest.mark.unit
    def test_metrics_module_importable(self) -> None:
        import fertility_sense.metrics as m

        # Should have the HAS_PROMETHEUS flag
        assert isinstance(m.HAS_PROMETHEUS, bool)


# ---------------------------------------------------------------------------
# 5. API error handlers
# ---------------------------------------------------------------------------


class TestAPIErrorHandlers:
    @pytest.mark.unit
    def test_status_code_mapping(self) -> None:
        from fertility_sense.api_errors import _status_code

        assert _status_code("FEED_INGESTION_ERROR") == 502
        assert _status_code("GOVERNANCE_VIOLATION") == 422
        assert _status_code("BUDGET_EXCEEDED") == 429
        assert _status_code("CONFIGURATION_ERROR") == 500
        assert _status_code("AGENT_DISPATCH_ERROR") == 502
        assert _status_code("UNKNOWN_CODE") == 500

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_handler_response(self) -> None:
        from fertility_sense.api_errors import fertility_sense_error_handler

        exc = FeedIngestionError("reddit", "connection refused")
        request = MagicMock()
        response = await fertility_sense_error_handler(request, exc)
        assert response.status_code == 502
        body = json.loads(response.body)
        assert body["error"] == "FEED_INGESTION_ERROR"
        assert body["details"]["feed"] == "reddit"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_governance_violation_handler(self) -> None:
        from fertility_sense.api_errors import fertility_sense_error_handler

        exc = GovernanceViolationError("t_001", ["diagnosis"])
        request = MagicMock()
        response = await fertility_sense_error_handler(request, exc)
        assert response.status_code == 422
        body = json.loads(response.body)
        assert body["error"] == "GOVERNANCE_VIOLATION"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_budget_exceeded_handler(self) -> None:
        from fertility_sense.api_errors import fertility_sense_error_handler

        exc = BudgetExceededError(budget=10.0, spent=10.5)
        request = MagicMock()
        response = await fertility_sense_error_handler(request, exc)
        assert response.status_code == 429
