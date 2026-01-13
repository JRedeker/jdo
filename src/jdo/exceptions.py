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
    ├── AuthError            # API key, credential issues
    └── TUIError             # Textual, widget issues
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Maximum length for raw response in context (truncate to avoid huge logs)
MAX_RAW_RESPONSE_LENGTH = 500

# Template for credential recovery hints
_CREDENTIAL_RECOVERY_HINT_TEMPLATE = "Run 'jdo auth' to {action} your {provider} API key."


@dataclass
class ErrorContext:
    """Structured context for exception debugging information.

    Provides type-safe context information for exceptions while maintaining
    backward compatibility with dictionary-based access.
    """

    provider: str | None = None
    status_code: int | None = None
    expected_type: str | None = None
    raw_response: str | None = None
    supported_providers: list[str] | None = None
    _extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for backward compatibility."""
        result: dict[str, Any] = self._extra.copy()
        if self.provider is not None:
            result["provider"] = self.provider
        if self.status_code is not None:
            result["status_code"] = self.status_code
        if self.expected_type is not None:
            result["expected_type"] = self.expected_type
        if self.raw_response is not None:
            result["raw_response"] = self.raw_response
        if self.supported_providers is not None:
            result["supported_providers"] = self.supported_providers
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ErrorContext:
        """Create ErrorContext from dictionary for backward compatibility."""
        if data is None:
            return cls()
        return cls(
            provider=data.get("provider"),
            status_code=data.get("status_code"),
            expected_type=data.get("expected_type"),
            raw_response=data.get("raw_response"),
            supported_providers=data.get("supported_providers"),
            _extra={
                k: v
                for k, v in data.items()
                if k
                not in {
                    "provider",
                    "status_code",
                    "expected_type",
                    "raw_response",
                    "supported_providers",
                }
            },
        )


def _format_credential_recovery_hint(provider: str, action: str) -> str:
    return _CREDENTIAL_RECOVERY_HINT_TEMPLATE.format(provider=provider, action=action)


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
        context: dict[str, Any] | ErrorContext | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: The error message.
            recovery_hint: Optional hint for users on how to resolve the error.
            context: Optional dictionary or ErrorContext of additional context for debugging.
        """
        super().__init__(message)
        self.message = message
        self.recovery_hint = recovery_hint
        if isinstance(context, ErrorContext):
            self.context = context.to_dict()
        else:
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
        context: dict[str, Any] | ErrorContext | None = None,
    ) -> None:
        """Initialize provider error with additional context.

        Args:
            message: The error message.
            provider: Name of the AI provider (e.g., "anthropic", "openai").
            status_code: HTTP status code if applicable.
            recovery_hint: Optional hint for users on how to resolve the error.
            context: Optional dictionary or ErrorContext of additional context for debugging.
        """
        ctx_obj = ErrorContext.from_dict(context) if isinstance(context, dict) else context
        ctx_obj = ctx_obj or ErrorContext()
        ctx_obj.provider = provider
        ctx_obj.status_code = status_code

        super().__init__(message, recovery_hint=recovery_hint, context=ctx_obj)
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
        context: dict[str, Any] | ErrorContext | None = None,
    ) -> None:
        """Initialize extraction error with additional context.

        Args:
            message: The error message.
            expected_type: The type/schema that was expected.
            raw_response: The raw response that failed to parse.
            recovery_hint: Optional hint for users on how to resolve the error.
            context: Optional dictionary or ErrorContext of additional context for debugging.
        """
        ctx_obj = ErrorContext.from_dict(context) if isinstance(context, dict) else context
        ctx_obj = ctx_obj or ErrorContext()
        ctx_obj.expected_type = expected_type
        if raw_response:
            ctx_obj.raw_response = (
                raw_response[:MAX_RAW_RESPONSE_LENGTH]
                if len(raw_response) > MAX_RAW_RESPONSE_LENGTH
                else raw_response
            )

        super().__init__(message, recovery_hint=recovery_hint, context=ctx_obj)
        self.expected_type = expected_type
        self.raw_response = raw_response


# Authentication Errors


class AuthError(JDOError):
    """Exception for authentication and authorization errors.

    Raised when:
    - API keys are missing or invalid
    - Credentials are expired
    - Permission denied
    """


class MissingCredentialsError(AuthError):
    """Exception raised when no credentials are available for the configured provider.

    Raised when:
    - No stored credentials exist for the configured AI provider
    - Environment variable fallback is disabled
    - User needs to configure credentials via 'jdo auth'
    """

    def __init__(
        self,
        provider: str,
        *,
        recovery_hint: str | None = None,
        context: dict[str, Any] | ErrorContext | None = None,
    ) -> None:
        """Initialize missing credentials error.

        Args:
            provider: The AI provider that lacks credentials.
            recovery_hint: Optional hint for users on how to resolve the error.
            context: Optional dictionary or ErrorContext of additional context for debugging.
        """
        msg = f"No credentials configured for AI provider: {provider}"
        hint = recovery_hint or _format_credential_recovery_hint(provider, "configure")
        ctx_obj = ErrorContext.from_dict(context) if isinstance(context, dict) else context
        ctx_obj = ctx_obj or ErrorContext()
        ctx_obj.provider = provider

        super().__init__(msg, recovery_hint=hint, context=ctx_obj)
        self.provider = provider


class InvalidCredentialsError(AuthError):
    """Exception raised when credentials have invalid format.

    Raised when:
    - API key format is invalid for the provider
    - Credential validation fails
    """

    def __init__(
        self,
        provider: str,
        *,
        recovery_hint: str | None = None,
        context: dict[str, Any] | ErrorContext | None = None,
    ) -> None:
        """Initialize invalid credentials error.

        Args:
            provider: The AI provider with invalid credentials.
            recovery_hint: Optional hint for users on how to resolve the error.
            context: Optional dictionary or ErrorContext of additional context for debugging.
        """
        msg = f"Invalid credentials format for AI provider: {provider}"
        hint = recovery_hint or _format_credential_recovery_hint(provider, "reconfigure")
        ctx_obj = ErrorContext.from_dict(context) if isinstance(context, dict) else context
        ctx_obj = ctx_obj or ErrorContext()
        ctx_obj.provider = provider

        super().__init__(msg, recovery_hint=hint, context=ctx_obj)
        self.provider = provider


class UnsupportedProviderError(ConfigError):
    """Exception raised when an unsupported AI provider is configured.

    Raised when:
    - Provider is not in the supported list (openai, anthropic, google, openrouter)
    - Provider configuration is invalid
    """

    def __init__(
        self,
        provider: str,
        *,
        recovery_hint: str | None = None,
        context: dict[str, Any] | ErrorContext | None = None,
    ) -> None:
        """Initialize unsupported provider error.

        Args:
            provider: The unsupported provider name.
            recovery_hint: Optional hint for users on how to resolve the error.
            context: Optional dictionary or ErrorContext of additional context for debugging.
        """
        supported = ["openai", "anthropic", "google", "openrouter"]
        msg = f"Unsupported AI provider: {provider}. Supported: {', '.join(supported)}"
        hint = recovery_hint or f"Set JDO_AI_PROVIDER to one of: {', '.join(supported)}"
        ctx_obj = ErrorContext.from_dict(context) if isinstance(context, dict) else context
        ctx_obj = ctx_obj or ErrorContext()
        ctx_obj.provider = provider
        ctx_obj.supported_providers = supported

        super().__init__(msg, recovery_hint=hint, context=ctx_obj)
        self.provider = provider
        self.supported_providers = supported


# TUI Errors


class TUIError(JDOError):
    """Exception for TUI/Textual errors.

    Raised when:
    - Widget initialization fails
    - Screen transitions fail
    - User input handling fails
    """
