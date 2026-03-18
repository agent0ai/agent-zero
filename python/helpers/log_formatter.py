"""
Structured JSON logging formatter for Agent Zero.

Provides JSON logging output compatible with log aggregation systems.
"""

import json
import logging
import time
import uuid
from typing import Any, Dict, Optional
from contextvars import ContextVar

from .log import Log

# Context variable to hold trace ID for request correlation
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)


def get_trace_id() -> str:
    """Get current trace ID or generate new one."""
    trace_id = trace_id_var.get()
    if trace_id is None:
        trace_id = str(uuid.uuid4())
        trace_id_var.set(trace_id)
    return trace_id


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""

    def __init__(
        self,
        include_trace_id: bool = True,
        include_context: bool = True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.include_trace_id = include_trace_id
        self.include_context = include_context

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        # Basic log data
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add stack info if present
        if record.stack_info:
            log_data["stack_info"] = record.stack_info

        # Include trace ID for correlation
        if self.include_trace_id:
            log_data["trace_id"] = get_trace_id()

        # Include Agent Zero context if available
        if self.include_context and hasattr(record, "agent_context"):
            ctx = record.agent_context
            log_data["context"] = {
                "id": ctx.id,
                "agent_no": ctx.streaming_agent.number if ctx.streaming_agent else 0,
            }

        # Include any extra attributes
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "getMessage",
                "asctime", "agent_context"
            ]:
                log_data[key] = value

        return json.dumps(log_data, default=str, ensure_ascii=False)


def setup_json_logging(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
    stream=None
) -> None:
    """
    Configure a logger to use JSON formatting.

    Args:
        logger: Logger to configure (defaults to root logger)
        level: Log level
        stream: Output stream (defaults to stderr)
    """
    if logger is None:
        logger = logging.getLogger()

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create new handler with JSON formatter
    import sys
    handler = logging.StreamHandler(stream or sys.stderr)
    formatter = JsonFormatter(
        fmt="%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S.%fZ"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

    # Also configure uvicorn/fastapi loggers
    for name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
        log = logging.getLogger(name)
        log.handlers = []
        log.addHandler(handler)
        log.setLevel(level)


def log_with_context(logger: logging.Logger, level: int, msg: str, **kwargs) -> None:
    """
    Log a message with Agent Zero context information.

    Args:
        logger: Logger to use
        level: Log level (e.g., logging.INFO)
        msg: Message to log
        **kwargs: Additional fields to include in log
    """
    try:
        from agent import AgentContext
        ctx = AgentContext.current()
        if ctx:
            kwargs["agent_context"] = ctx
    except Exception:
        pass

    logger.log(level, msg, extra=kwargs)


# Convenience functions
def info(msg: str, **kwargs):
    log_with_context(logging.getLogger("agent-zero"), logging.INFO, msg, **kwargs)


def warning(msg: str, **kwargs):
    log_with_context(logging.getLogger("agent-zero"), logging.WARNING, msg, **kwargs)


def error(msg: str, **kwargs):
    log_with_context(logging.getLogger("agent-zero"), logging.ERROR, msg, **kwargs)


def debug(msg: str, **kwargs):
    log_with_context(logging.getLogger("agent-zero"), logging.DEBUG, msg, **kwargs)


def critical(msg: str, **kwargs):
    log_with_context(logging.getLogger("agent-zero"), logging.CRITICAL, msg, **kwargs)
