"""FHIR R4 Audit Logger for HIPAA-compliant access logging.

This module provides async audit logging with configurable outputs
including file, stdout, and external services.
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from fhir_r4_mcp.audit.events import (
    AuditEvent,
    AuditOutcome,
    AuditSubtype,
    create_audit_event,
)
from fhir_r4_mcp.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AuditConfig:
    """Configuration for audit logging."""

    enabled: bool = True
    output: str = "file"  # file, stdout, both, none
    file_path: str | None = None
    file_rotation: bool = True
    max_file_size_mb: int = 100
    include_fhir_format: bool = False  # Include full FHIR AuditEvent format
    async_logging: bool = True  # Use async logging to avoid blocking

    def __post_init__(self) -> None:
        """Set default file path if not provided."""
        if self.output in ("file", "both") and not self.file_path:
            self.file_path = os.getenv(
                "FHIR_AUDIT_LOG_PATH",
                str(Path.home() / ".fhir-r4-mcp" / "audit.log"),
            )


class AuditLogger:
    """HIPAA-compliant audit logger.

    Provides async audit logging for FHIR operations with
    configurable output destinations.
    """

    def __init__(self, config: AuditConfig | None = None) -> None:
        """Initialize the audit logger.

        Args:
            config: Audit configuration, uses defaults if not provided.
        """
        self._config = config or AuditConfig()
        self._queue: asyncio.Queue[AuditEvent] = asyncio.Queue()
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._file_handle: Any = None

    @property
    def enabled(self) -> bool:
        """Check if audit logging is enabled."""
        return self._config.enabled

    async def start(self) -> None:
        """Start the async audit logging worker."""
        if self._running:
            return

        self._running = True

        # Ensure log directory exists
        if self._config.output in ("file", "both") and self._config.file_path:
            log_dir = Path(self._config.file_path).parent
            log_dir.mkdir(parents=True, exist_ok=True)

        if self._config.async_logging:
            self._task = asyncio.create_task(self._worker())
            logger.debug("Audit logger worker started")

    async def stop(self) -> None:
        """Stop the async audit logging worker."""
        self._running = False

        if self._task:
            # Wait for queue to drain
            await self._queue.join()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None

        logger.debug("Audit logger worker stopped")

    async def _worker(self) -> None:
        """Background worker to process audit events."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._write_event(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in audit logger worker: {e}")

    async def _write_event(self, event: AuditEvent) -> None:
        """Write an audit event to configured outputs."""
        try:
            if self._config.output in ("file", "both"):
                await self._write_to_file(event)

            if self._config.output in ("stdout", "both"):
                self._write_to_stdout(event)

        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")

    async def _write_to_file(self, event: AuditEvent) -> None:
        """Write event to log file."""
        if not self._config.file_path:
            return

        try:
            # Check file rotation
            if self._config.file_rotation:
                await self._check_rotation()

            # Format the log line
            if self._config.include_fhir_format:
                log_data = event.to_fhir()
            else:
                log_data = event.to_dict()

            log_line = json.dumps(log_data) + "\n"

            # Write to file (async-safe with run_in_executor)
            def write_sync() -> None:
                with open(self._config.file_path, "a") as f:  # type: ignore
                    f.write(log_line)

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, write_sync)

        except Exception as e:
            logger.error(f"Failed to write to audit log file: {e}")

    async def _check_rotation(self) -> None:
        """Check if log file needs rotation."""
        if not self._config.file_path:
            return

        try:
            path = Path(self._config.file_path)
            if path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
                if size_mb >= self._config.max_file_size_mb:
                    # Rotate the file
                    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                    rotated_path = path.with_suffix(f".{timestamp}.log")
                    path.rename(rotated_path)
                    logger.info(f"Rotated audit log to {rotated_path}")

        except Exception as e:
            logger.error(f"Failed to rotate audit log: {e}")

    def _write_to_stdout(self, event: AuditEvent) -> None:
        """Write event to stdout."""
        log_data = event.to_dict()
        print(f"[AUDIT] {json.dumps(log_data)}")  # noqa: T201

    async def log(self, event: AuditEvent) -> None:
        """Log an audit event.

        Args:
            event: The audit event to log.
        """
        if not self._config.enabled:
            return

        if self._config.async_logging:
            # Add to queue for async processing
            await self._queue.put(event)
        else:
            # Write synchronously
            await self._write_event(event)

    async def log_operation(
        self,
        subtype: AuditSubtype,
        outcome: AuditOutcome,
        connection_id: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        query: str | None = None,
        outcome_desc: str | None = None,
        user: str | None = None,
    ) -> None:
        """Log a FHIR operation.

        Convenience method to create and log an audit event.

        Args:
            subtype: The FHIR interaction subtype
            outcome: The outcome of the operation
            connection_id: The FHIR connection ID
            resource_type: The resource type accessed
            resource_id: The resource ID accessed
            query: Search query string
            outcome_desc: Description of outcome
            user: User identifier
        """
        event = create_audit_event(
            subtype=subtype,
            outcome=outcome,
            connection_id=connection_id,
            resource_type=resource_type,
            resource_id=resource_id,
            query=query,
            outcome_desc=outcome_desc,
            user=user,
        )
        await self.log(event)


# Global audit logger instance
audit_logger = AuditLogger()


def audit_tool(
    subtype: AuditSubtype,
    resource_type: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator for auditing MCP tool calls.

    This decorator wraps tool functions to automatically log
    audit events before and after execution.

    Args:
        subtype: The FHIR interaction subtype for this tool
        resource_type: Optional resource type being accessed

    Returns:
        Decorated function with audit logging

    Example:
        @mcp.tool()
        @audit_tool(AuditSubtype.SEARCH, resource_type="Patient")
        async def fhir_patient_search(...):
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Extract connection_id from kwargs or args
            connection_id = kwargs.get("connection_id", "unknown")

            # Extract resource_id if present
            resource_id = kwargs.get("resource_id") or kwargs.get("patient_id")

            # Extract query params for search operations
            query = None
            if subtype == AuditSubtype.SEARCH:
                # Build query string from parameters
                search_params = {
                    k: v
                    for k, v in kwargs.items()
                    if k not in ("connection_id", "validate") and v is not None
                }
                if search_params:
                    query = "&".join(f"{k}={v}" for k, v in search_params.items())

            # Determine the actual resource type
            rt = resource_type or kwargs.get("resource_type")

            try:
                # Execute the tool
                result = await func(*args, **kwargs)

                # Log success
                outcome = AuditOutcome.SUCCESS
                outcome_desc = None

                # Check if result indicates an error
                if isinstance(result, dict) and not result.get("success", True):
                    outcome = AuditOutcome.MINOR_FAILURE
                    error_info = result.get("error", {})
                    outcome_desc = error_info.get("message")

                await audit_logger.log_operation(
                    subtype=subtype,
                    outcome=outcome,
                    connection_id=connection_id,
                    resource_type=rt,
                    resource_id=resource_id,
                    query=query,
                    outcome_desc=outcome_desc,
                )

                return result

            except Exception as e:
                # Log failure
                await audit_logger.log_operation(
                    subtype=subtype,
                    outcome=AuditOutcome.SERIOUS_FAILURE,
                    connection_id=connection_id,
                    resource_type=rt,
                    resource_id=resource_id,
                    query=query,
                    outcome_desc=str(e),
                )
                raise

        return wrapper

    return decorator


async def start_audit_logging(config: AuditConfig | None = None) -> None:
    """Start the global audit logger.

    Should be called at server startup.

    Args:
        config: Optional audit configuration
    """
    global audit_logger
    if config:
        audit_logger = AuditLogger(config)
    await audit_logger.start()


async def stop_audit_logging() -> None:
    """Stop the global audit logger.

    Should be called at server shutdown.
    """
    await audit_logger.stop()
