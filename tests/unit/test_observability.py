"""Tests for the observability module."""

from unittest.mock import MagicMock, patch

import pytest
import sentry_sdk

from jdo.exceptions import JDOError, ProviderError
from jdo.observability import (
    APP_VERSION,
    add_breadcrumb,
    capture_exception,
    enrich_error_context,
    init_sentry,
    set_user_context,
    start_transaction,
)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = MagicMock()
    settings.sentry_dsn = None
    settings.sentry_traces_sample_rate = 0.1
    settings.environment = "test"
    return settings


class TestInitSentry:
    """Tests for init_sentry function."""

    def test_skips_init_when_no_dsn(self, mock_settings):
        """init_sentry returns False when no DSN configured."""
        result = init_sentry(mock_settings)

        assert result is False

    @patch("jdo.observability.sentry_sdk.init")
    def test_initializes_when_dsn_provided(self, mock_init, mock_settings):
        """init_sentry calls sentry_sdk.init when DSN is configured."""
        mock_settings.sentry_dsn = "https://test@sentry.io/123"

        result = init_sentry(mock_settings)

        assert result is True
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["dsn"] == "https://test@sentry.io/123"
        assert call_kwargs["environment"] == "test"
        assert f"jdo@{APP_VERSION}" in call_kwargs["release"]

    @patch("jdo.observability.sentry_sdk.init")
    def test_uses_custom_sample_rate(self, mock_init, mock_settings):
        """init_sentry uses configured traces_sample_rate."""
        mock_settings.sentry_dsn = "https://test@sentry.io/123"
        mock_settings.sentry_traces_sample_rate = 0.5

        init_sentry(mock_settings)

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs["traces_sample_rate"] == 0.5


class TestCaptureException:
    """Tests for capture_exception function."""

    @patch("jdo.observability.sentry_sdk.capture_exception")
    def test_captures_simple_exception(self, mock_capture):
        """capture_exception forwards to sentry_sdk."""
        mock_capture.return_value = "event-123"
        error = ValueError("test error")

        result = capture_exception(error)

        mock_capture.assert_called_once_with(error)
        assert result == "event-123"

    @patch("jdo.observability.sentry_sdk.push_scope")
    @patch("jdo.observability.sentry_sdk.capture_exception")
    def test_captures_with_context(self, mock_capture, mock_push_scope):
        """capture_exception adds context when provided."""
        mock_capture.return_value = "event-456"
        mock_scope = MagicMock()
        mock_push_scope.return_value.__enter__ = MagicMock(return_value=mock_scope)
        mock_push_scope.return_value.__exit__ = MagicMock(return_value=False)

        error = ValueError("test")
        context = {"user_id": "123", "action": "save"}

        capture_exception(error, context=context)

        mock_scope.set_extra.assert_any_call("user_id", "123")
        mock_scope.set_extra.assert_any_call("action", "save")


class TestAddBreadcrumb:
    """Tests for add_breadcrumb function."""

    @patch("jdo.observability.sentry_sdk.add_breadcrumb")
    def test_adds_basic_breadcrumb(self, mock_add):
        """add_breadcrumb forwards to sentry_sdk."""
        add_breadcrumb("User clicked button", category="ui")

        mock_add.assert_called_once_with(
            message="User clicked button",
            category="ui",
            level="info",
            data=None,
        )

    @patch("jdo.observability.sentry_sdk.add_breadcrumb")
    def test_adds_breadcrumb_with_data(self, mock_add):
        """add_breadcrumb includes data when provided."""
        add_breadcrumb(
            "AI extraction completed",
            category="ai",
            level="info",
            data={"model": "claude-3", "tokens": 150},
        )

        mock_add.assert_called_once()
        call_kwargs = mock_add.call_args.kwargs
        assert call_kwargs["data"] == {"model": "claude-3", "tokens": 150}


class TestSetUserContext:
    """Tests for set_user_context function."""

    @patch("jdo.observability.sentry_sdk.set_user")
    def test_sets_user_with_id(self, mock_set_user):
        """set_user_context sets user with ID."""
        set_user_context(user_id="user-123")

        mock_set_user.assert_called_once_with({"id": "user-123", "email": None})

    @patch("jdo.observability.sentry_sdk.set_user")
    def test_sets_user_with_email(self, mock_set_user):
        """set_user_context sets user with email."""
        set_user_context(email="test@example.com")

        mock_set_user.assert_called_once_with({"id": None, "email": "test@example.com"})

    @patch("jdo.observability.sentry_sdk.set_user")
    def test_clears_user_when_no_args(self, mock_set_user):
        """set_user_context clears user when no args provided."""
        set_user_context()

        mock_set_user.assert_called_once_with(None)


class TestStartTransaction:
    """Tests for start_transaction function."""

    @patch("jdo.observability.sentry_sdk.start_transaction")
    def test_starts_transaction(self, mock_start):
        """start_transaction forwards to sentry_sdk."""
        start_transaction("extract_commitment", "ai")

        mock_start.assert_called_once_with(name="extract_commitment", op="ai")

    @patch("jdo.observability.sentry_sdk.start_transaction")
    def test_default_op_is_task(self, mock_start):
        """start_transaction uses 'task' as default op."""
        start_transaction("my_operation")

        call_kwargs = mock_start.call_args.kwargs
        assert call_kwargs["op"] == "task"


class TestEnrichErrorContext:
    """Tests for enrich_error_context function."""

    @patch("jdo.observability.sentry_sdk.set_context")
    def test_enriches_jdo_error(self, mock_set_context):
        """enrich_error_context adds JDOError details."""
        error = JDOError(
            "Test error",
            recovery_hint="Try again",
            context={"key": "value"},
        )

        enrich_error_context(error)

        mock_set_context.assert_called_once()
        call_args = mock_set_context.call_args
        assert call_args[0][0] == "jdo_error"
        context_data = call_args[0][1]
        assert context_data["type"] == "JDOError"
        assert context_data["message"] == "Test error"
        assert context_data["recovery_hint"] == "Try again"
        assert context_data["key"] == "value"

    @patch("jdo.observability.sentry_sdk.set_context")
    def test_enriches_subclass_error(self, mock_set_context):
        """enrich_error_context works with JDOError subclasses."""
        error = ProviderError(
            "API rate limited",
            provider="anthropic",
            status_code=429,
        )

        enrich_error_context(error)

        call_args = mock_set_context.call_args
        context_data = call_args[0][1]
        assert context_data["type"] == "ProviderError"
        assert context_data["provider"] == "anthropic"
        assert context_data["status_code"] == 429

    @patch("jdo.observability.sentry_sdk.set_context")
    def test_ignores_non_jdo_error(self, mock_set_context):
        """enrich_error_context does nothing for non-JDO errors."""
        error = ValueError("standard error")

        enrich_error_context(error)

        mock_set_context.assert_not_called()


class TestAppVersion:
    """Tests for APP_VERSION constant."""

    def test_version_format(self):
        """APP_VERSION follows semver format."""
        parts = APP_VERSION.split(".")
        assert len(parts) == 3
        # All parts should be numeric
        for part in parts:
            assert part.isdigit()
