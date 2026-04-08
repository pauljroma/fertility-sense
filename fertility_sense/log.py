"""Structured JSON logging with request context."""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

import structlog

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
agent_name_var: ContextVar[str] = ContextVar("agent_name", default="")


def _add_context_vars(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Inject request-scoped context vars into every log event."""
    rid = request_id_var.get("")
    if rid:
        event_dict["request_id"] = rid
    agent = agent_name_var.get("")
    if agent:
        event_dict["agent_name"] = agent
    return event_dict


def setup_logging(
    level: str = "INFO",
    json_output: bool = True,
) -> structlog.BoundLogger:
    """Configure structlog with JSON (production) or console (dev) rendering.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_output: If True, render as JSON lines; otherwise use coloured console.

    Returns:
        A bound structlog logger.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_context_vars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_output:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Also wire stdlib logging through structlog
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Replace existing handlers
    root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    return structlog.get_logger("fertility_sense")
