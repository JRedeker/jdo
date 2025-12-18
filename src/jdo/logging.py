"""Structured logging configuration using Loguru.

This module provides centralized logging configuration with:
- Console output with colored formatting
- Optional file output with JSON serialization
- Rotation and retention for log files
- Standard library logging interception
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, ClassVar

from loguru import logger

if TYPE_CHECKING:
    from pathlib import Path
    from types import FrameType

    import loguru


class InterceptHandler(logging.Handler):
    """Handler to intercept stdlib logging and redirect to Loguru.

    This allows third-party libraries using stdlib logging (httpx, sqlalchemy)
    to be captured by Loguru with consistent formatting.
    """

    # Mapping from stdlib log level names to Loguru levels
    LEVEL_MAP: ClassVar[dict[int, str]] = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record by forwarding to Loguru.

        Args:
            record: The stdlib log record to forward.
        """
        # Get corresponding Loguru level
        level = self.LEVEL_MAP.get(record.levelno, record.levelname)

        # Find caller from where the logged message originated
        frame: FrameType | None = sys._getframe(6)  # noqa: SLF001 - Required for correct frame depth
        depth = 6

        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# Console format: colored, human-readable
CONSOLE_FORMAT = (
    "<green>{time:HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def configure_logging(
    level: str = "INFO",
    log_file_path: Path | None = None,
    *,
    intercept_stdlib: bool = True,
) -> None:
    """Configure Loguru logging for the application.

    Sets up console output and optional file logging with rotation.
    Can optionally intercept stdlib logging from third-party libraries.

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file_path: Optional path for file logging with JSON serialization.
        intercept_stdlib: Whether to intercept stdlib logging.
    """
    # Remove default handler
    logger.remove()

    # Add console handler with colored output
    logger.add(
        sys.stderr,
        format=CONSOLE_FORMAT,
        level=level,
        colorize=True,
    )

    # Add file handler if path provided
    if log_file_path:
        logger.add(
            log_file_path,
            level=level,
            serialize=True,  # JSON format for production
            rotation="10 MB",  # Rotate when file reaches 10MB
            retention="7 days",  # Keep logs for 7 days
            compression="gz",  # Compress rotated logs
        )

    # Intercept stdlib logging
    if intercept_stdlib:
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

        # Explicitly intercept common libraries
        for logger_name in ["httpx", "sqlalchemy", "textual", "pydantic_ai"]:
            logging.getLogger(logger_name).handlers = [InterceptHandler()]


def get_logger(name: str) -> loguru.Logger:
    """Get a logger instance bound to a module name.

    Args:
        name: Module name (typically __name__).

    Returns:
        A Loguru logger bound to the given name.
    """
    return logger.bind(name=name)
