"""Logging configuration using structlog."""
import logging
import sys
from pathlib import Path
from typing import Any
import structlog
from config import settings, BASE_DIR


def setup_logging() -> None:
    """Configure structlog for the application."""
    # Create logs directory if it doesn't exist
    log_dir = BASE_DIR / settings.logging.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.logging.level.upper()),
    )

    # Processors for structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Add JSON or console renderer based on settings
    if settings.logging.log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Add file handler if enabled
    if settings.logging.log_to_file:
        log_file = log_dir / settings.logging.log_file
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, settings.logging.level.upper()))
        logging.root.addHandler(file_handler)


def get_logger(name: str) -> Any:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)
