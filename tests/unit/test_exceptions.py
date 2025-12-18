"""Tests for the custom exception hierarchy."""

import pytest

from jdo.exceptions import (
    AIError,
    AuthError,
    ConfigError,
    DatabaseError,
    ExtractionError,
    JDOError,
    MigrationError,
    ProviderError,
    TUIError,
)


class TestJDOError:
    """Tests for the base JDOError class."""

    def test_basic_message(self):
        """JDOError stores and returns the message."""
        error = JDOError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"

    def test_with_recovery_hint(self):
        """JDOError includes recovery hint in string representation."""
        error = JDOError("Database connection failed", recovery_hint="Check your connection")

        assert "Database connection failed" in str(error)
        assert "Check your connection" in str(error)
        assert error.recovery_hint == "Check your connection"

    def test_with_context(self):
        """JDOError stores additional context."""
        context = {"user_id": "123", "action": "save"}
        error = JDOError("Operation failed", context=context)

        assert error.context == {"user_id": "123", "action": "save"}

    def test_empty_context_default(self):
        """JDOError defaults to empty context dict."""
        error = JDOError("Error")

        assert error.context == {}

    def test_is_exception(self):
        """JDOError is a proper Exception."""
        error = JDOError("Test")

        assert isinstance(error, Exception)

        with pytest.raises(JDOError):
            raise error


class TestConfigError:
    """Tests for ConfigError."""

    def test_inherits_from_jdo_error(self):
        """ConfigError inherits from JDOError."""
        error = ConfigError("Invalid config")

        assert isinstance(error, JDOError)
        assert isinstance(error, Exception)

    def test_catchable_as_jdo_error(self):
        """ConfigError can be caught as JDOError."""
        with pytest.raises(JDOError):
            raise ConfigError("Missing env var")

    def test_with_recovery_hint(self):
        """ConfigError supports recovery hints."""
        error = ConfigError("Missing API key", recovery_hint="Set JDO_API_KEY environment variable")

        assert "Missing API key" in str(error)
        assert error.recovery_hint == "Set JDO_API_KEY environment variable"


class TestDatabaseError:
    """Tests for DatabaseError and MigrationError."""

    def test_database_error_inherits(self):
        """DatabaseError inherits from JDOError."""
        error = DatabaseError("Connection failed")

        assert isinstance(error, JDOError)

    def test_migration_error_inherits_from_database_error(self):
        """MigrationError inherits from DatabaseError."""
        error = MigrationError("Schema conflict")

        assert isinstance(error, DatabaseError)
        assert isinstance(error, JDOError)

    def test_catch_migration_as_database_error(self):
        """MigrationError can be caught as DatabaseError."""
        with pytest.raises(DatabaseError):
            raise MigrationError("Migration failed")


class TestAIError:
    """Tests for AIError hierarchy."""

    def test_ai_error_inherits(self):
        """AIError inherits from JDOError."""
        error = AIError("AI processing failed")

        assert isinstance(error, JDOError)

    def test_provider_error_inherits(self):
        """ProviderError inherits from AIError."""
        error = ProviderError("API rate limit")

        assert isinstance(error, AIError)
        assert isinstance(error, JDOError)

    def test_provider_error_with_details(self):
        """ProviderError stores provider and status code."""
        error = ProviderError(
            "Rate limit exceeded",
            provider="anthropic",
            status_code=429,
            recovery_hint="Wait 60 seconds before retrying",
        )

        assert error.provider == "anthropic"
        assert error.status_code == 429
        assert error.context["provider"] == "anthropic"
        assert error.context["status_code"] == 429
        assert error.recovery_hint == "Wait 60 seconds before retrying"

    def test_extraction_error_inherits(self):
        """ExtractionError inherits from AIError."""
        error = ExtractionError("Invalid response format")

        assert isinstance(error, AIError)
        assert isinstance(error, JDOError)

    def test_extraction_error_with_details(self):
        """ExtractionError stores expected type and raw response."""
        error = ExtractionError(
            "Failed to parse",
            expected_type="Commitment",
            raw_response='{"invalid": "data"}',
        )

        assert error.expected_type == "Commitment"
        assert error.raw_response == '{"invalid": "data"}'
        assert error.context["expected_type"] == "Commitment"

    def test_extraction_error_truncates_long_response(self):
        """ExtractionError truncates long raw responses in context."""
        long_response = "x" * 1000
        error = ExtractionError("Failed", raw_response=long_response)

        assert len(error.context["raw_response"]) == 500
        assert error.raw_response == long_response  # Original preserved

    def test_catch_provider_as_ai_error(self):
        """ProviderError can be caught as AIError."""
        with pytest.raises(AIError):
            raise ProviderError("API failed")

    def test_catch_extraction_as_ai_error(self):
        """ExtractionError can be caught as AIError."""
        with pytest.raises(AIError):
            raise ExtractionError("Parse failed")


class TestAuthError:
    """Tests for AuthError."""

    def test_inherits_from_jdo_error(self):
        """AuthError inherits from JDOError."""
        error = AuthError("Token expired")

        assert isinstance(error, JDOError)

    def test_with_recovery_hint(self):
        """AuthError supports recovery hints."""
        error = AuthError("OAuth flow failed", recovery_hint="Try logging in again")

        assert error.recovery_hint == "Try logging in again"


class TestTUIError:
    """Tests for TUIError."""

    def test_inherits_from_jdo_error(self):
        """TUIError inherits from JDOError."""
        error = TUIError("Widget failed to render")

        assert isinstance(error, JDOError)


class TestErrorHierarchy:
    """Tests for the complete exception hierarchy."""

    def test_all_errors_are_jdo_errors(self):
        """All custom exceptions inherit from JDOError."""
        exceptions = [
            ConfigError("config"),
            DatabaseError("db"),
            MigrationError("migration"),
            AIError("ai"),
            ProviderError("provider"),
            ExtractionError("extraction"),
            AuthError("auth"),
            TUIError("tui"),
        ]

        for error in exceptions:
            assert isinstance(error, JDOError), f"{type(error).__name__} is not a JDOError"

    def test_catch_all_jdo_errors(self):
        """All custom exceptions can be caught with JDOError."""
        exception_classes = [
            ConfigError,
            DatabaseError,
            MigrationError,
            AIError,
            ProviderError,
            ExtractionError,
            AuthError,
            TUIError,
        ]

        for exc_class in exception_classes:
            with pytest.raises(JDOError):
                raise exc_class("test")
