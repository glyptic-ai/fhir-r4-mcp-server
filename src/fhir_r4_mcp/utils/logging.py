"""Logging utilities for FHIR R4 MCP Server."""

import logging
import os
import sys
from typing import Any


def setup_logging(
    level: str | None = None,
    format_string: str | None = None,
) -> logging.Logger:
    """
    Set up logging for the FHIR R4 MCP Server.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to FHIR_LOG_LEVEL env var or INFO.
        format_string: Custom format string for log messages.

    Returns:
        Configured logger instance.
    """
    log_level = level or os.environ.get("FHIR_LOG_LEVEL", "INFO").upper()

    # Default format includes timestamp, level, and message
    default_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_format = format_string or default_format

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        stream=sys.stderr,  # MCP servers should log to stderr, not stdout
    )

    # Create and return the FHIR MCP logger
    logger = logging.getLogger("fhir_r4_mcp")
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Module name (typically __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(f"fhir_r4_mcp.{name}")


class LogContext:
    """Context manager for adding contextual information to log messages."""

    def __init__(self, logger: logging.Logger, **context: Any) -> None:
        """
        Initialize log context.

        Args:
            logger: Logger instance to use.
            **context: Key-value pairs to include in log messages.
        """
        self.logger = logger
        self.context = context

    def _format_context(self) -> str:
        """Format context as a string."""
        if not self.context:
            return ""
        parts = [f"{k}={v}" for k, v in self.context.items()]
        return f"[{', '.join(parts)}] "

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with context."""
        self.logger.debug(f"{self._format_context()}{message}", **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with context."""
        self.logger.info(f"{self._format_context()}{message}", **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with context."""
        self.logger.warning(f"{self._format_context()}{message}", **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with context."""
        self.logger.error(f"{self._format_context()}{message}", **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception message with context and stack trace."""
        self.logger.exception(f"{self._format_context()}{message}", **kwargs)


# Initialize default logger
logger = setup_logging()
