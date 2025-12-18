"""Custom exception hierarchy for JDO application.

This module defines a domain-based exception hierarchy that enables:
- Clear error categorization for handling and recovery
- Recovery hints for user-facing error messages
- Consistent logging and error tracking
- Domain-specific catch-all handlers

Hierarchy:
    JDOError (base)
    ├── ConfigError          # Settings, environment issues
    ├── DatabaseError        # SQLModel, SQLite issues
    │   └── MigrationError   # Alembic-specific
    ├── AIError              # Provider, model, tool issues
    │   ├── ProviderError    # API failures
    │   └── ExtractionError  # Response parsing
    ├── AuthError            # OAuth, token issues
    └── TUIError             # Textual, widget issues
"""

from __future__ import annotations

from typing import Any

# Maximum length for raw response in context (truncate to avoid huge logs)
MAX_RAW_RESPONSE_LENGTH = 500


class JDOError(Exception):
    """Base exception for all JDO application errors.

    All JDO-specific exceptions should inherit from this class
    to enable catch-all error handling.

    Attributes:
        message: The error message.
        recovery_hint: Optional hint for users on how to resolve the error.
        context: Optional dictionary of additional context for debugging.
    """

    def __init__(
        self,
        message: str,
        *,
        recovery_hint: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            recovery_hint: Optional hint for users on how to resolve the error.
            context: Optional dictionary of additional context for debugging.
        """
        super().__init__(message)
        self.message = message
        self.recovery_hint = recovery_hint
        self.context = context or {}

    def __str__(self) -> str:
        """Return string representation including recovery hint if present."""
        if self.recovery_hint:
            return f"{self.message}\n\nRecovery hint: {self.recovery_hint}"
        return self.message


# Configuration Errors


class ConfigError(JDOError):
    """Exception for configuration and settings errors.

    Raised when:
    - Required environment variables are missing
    - Configuration files are malformed
    - Invalid setting values are provided
    """


# Database Errors


class DatabaseError(JDOError):
    """Exception for database operations.

    Raised when:
    - Database connection fails
    - Query execution fails
    - Transaction errors occur
    """


class MigrationError(DatabaseError):
    """Exception for database migration errors.

    Raised when:
    - Migration script fails
    - Schema conflicts occur
    - Rollback is needed
    """


# AI/LLM Errors


class AIError(JDOError):
    """Base exception for AI-related errors.

    Raised when:
    - AI operations fail in an unspecified way
    - General AI processing errors occur
    """


class ProviderError(AIError):
    """Exception for AI provider API errors.

    Raised when:
    - API rate limits are hit
    - Authentication fails
    - Network errors occur
    - Provider service is unavailable
    """

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        status_code: int | None = None,
        recovery_hint: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize provider error with additional context.

        Args:
            message: The error message.
            provider: Name of the AI provider (e.g., "anthropic", "openai").
            status_code: HTTP status code if applicable.
            recovery_hint: Optional hint for users on how to resolve the error.
            context: Optional dictionary of additional context for debugging.
        """
        ctx = context or {}
        if provider:
            ctx["provider"] = provider
        if status_code:
            ctx["status_code"] = status_code

        super().__init__(message, recovery_hint=recovery_hint, context=ctx)
        self.provider = provider
        self.status_code = status_code


class ExtractionError(AIError):
    """Exception for AI response parsing/extraction errors.

    Raised when:
    - AI response doesn't match expected schema
    - Required fields are missing
    - Data validation fails
    """

    def __init__(
        self,
        message: str,
        *,
        expected_type: str | None = None,
        raw_response: str | None = None,
        recovery_hint: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize extraction error with additional context.

        Args:
            message: The error message.
            expected_type: The type/schema that was expected.
            raw_response: The raw response that failed to parse.
            recovery_hint: Optional hint for users on how to resolve the error.
            context: Optional dictionary of additional context for debugging.
        """
        ctx = context or {}
        if expected_type:
            ctx["expected_type"] = expected_type
        if raw_response:
            # Truncate long responses
            if len(raw_response) > MAX_RAW_RESPONSE_LENGTH:
                ctx["raw_response"] = raw_response[:MAX_RAW_RESPONSE_LENGTH]
            else:
                ctx["raw_response"] = raw_response

        super().__init__(message, recovery_hint=recovery_hint, context=ctx)
        self.expected_type = expected_type
        self.raw_response = raw_response


# Authentication Errors


class AuthError(JDOError):
    """Exception for authentication and authorization errors.

    Raised when:
    - OAuth flow fails
    - Tokens are expired or invalid
    - API keys are missing or invalid
    - Permission denied
    """


# TUI Errors


class TUIError(JDOError):
    """Exception for TUI/Textual errors.

    Raised when:
    - Widget initialization fails
    - Screen transitions fail
    - User input handling fails
    """
