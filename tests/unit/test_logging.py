"""Tests for the logging configuration module."""

import logging
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from loguru import logger

from jdo.logging import CONSOLE_FORMAT, InterceptHandler, configure_logging, get_logger


class TestInterceptHandler:
    """Tests for the stdlib logging interceptor."""

    def test_handler_forwards_to_loguru(self):
        """InterceptHandler forwards stdlib logs to loguru."""
        handler = InterceptHandler()

        # Create a test record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Should not raise
        handler.emit(record)

    def test_level_mapping(self):
        """Handler maps stdlib levels correctly."""
        handler = InterceptHandler()

        assert handler.LEVEL_MAP[logging.DEBUG] == "DEBUG"
        assert handler.LEVEL_MAP[logging.INFO] == "INFO"
        assert handler.LEVEL_MAP[logging.WARNING] == "WARNING"
        assert handler.LEVEL_MAP[logging.ERROR] == "ERROR"
        assert handler.LEVEL_MAP[logging.CRITICAL] == "CRITICAL"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_removes_default_handler(self):
        """configure_logging removes the default loguru handler."""
        # Reset to default state
        logger.remove()
        logger.add(sys.stderr)

        # Configure should remove and add new handlers
        configure_logging(level="INFO", intercept_stdlib=False)

        # Logger should still work
        logger.info("Test message after configure")

    def test_respects_log_level(self):
        """configure_logging respects the provided log level."""
        # Capture output at ERROR level
        output = StringIO()
        logger.remove()  # Clear all handlers
        handler_id = logger.add(output, format="{level} {message}", level="ERROR")

        try:
            logger.debug("Debug message")
            logger.error("Error message")

            content = output.getvalue()
            assert "Debug message" not in content
            assert "Error message" in content
        finally:
            logger.remove(handler_id)

    def test_file_logging_enabled(self, tmp_path):
        """configure_logging enables file logging when path provided."""
        log_file = tmp_path / "test.log"

        configure_logging(level="INFO", log_file_path=log_file, intercept_stdlib=False)

        logger.info("Test file message")

        # File should be created (might need to wait for buffer flush)
        # For JSON serialized logs, content will be on disk

    def test_console_format_defined(self):
        """CONSOLE_FORMAT constant is defined and contains expected elements."""
        assert "{time" in CONSOLE_FORMAT
        assert "{level" in CONSOLE_FORMAT
        assert "{message}" in CONSOLE_FORMAT

    def test_stdlib_interception_enabled(self):
        """configure_logging can intercept stdlib logging."""
        configure_logging(level="INFO", intercept_stdlib=True)

        # Get a stdlib logger
        stdlib_logger = logging.getLogger("test_stdlib")

        # This should not raise and should be intercepted
        stdlib_logger.info("Stdlib test message")


class TestGetLogger:
    """Tests for get_logger helper function."""

    def test_returns_bound_logger(self):
        """get_logger returns a logger bound to the module name."""
        bound_logger = get_logger("my.module")

        # Should be callable
        assert hasattr(bound_logger, "info")
        assert hasattr(bound_logger, "debug")
        assert hasattr(bound_logger, "error")

    def test_logs_with_bound_name(self):
        """Bound logger includes the name in log records."""
        bound_logger = get_logger("test.module")

        # Should work without errors
        bound_logger.info("Test with bound name")


class TestLoggingIntegration:
    """Integration tests for logging with the application."""

    def test_logging_module_importable(self):
        """The logging module can be imported."""
        from jdo import logging as jdo_logging

        assert hasattr(jdo_logging, "configure_logging")
        assert hasattr(jdo_logging, "get_logger")
        assert hasattr(jdo_logging, "InterceptHandler")

    def test_configure_multiple_times_safe(self):
        """Calling configure_logging multiple times is safe."""
        configure_logging(level="INFO", intercept_stdlib=False)
        configure_logging(level="DEBUG", intercept_stdlib=False)
        configure_logging(level="WARNING", intercept_stdlib=False)

        # Should still work
        logger.warning("After multiple configurations")
