"""Observability and error tracking with Sentry.

This module provides centralized Sentry initialization with:
- Optional activation (only when DSN is configured)
- Loguru integration for error forwarding
- Custom JDOError context enrichment
- AI call tracing
"""

import logging
from typing import TYPE_CHECKING, Any

import sentry_sdk
from loguru import logger
from sentry_sdk.integrations.loguru import LoguruIntegration
from sentry_sdk.tracing import NoOpSpan, Transaction

if TYPE_CHECKING:
    from jdo.config.settings import JDOSettings

# Application version for Sentry release tracking
APP_VERSION = "0.1.0"


def init_sentry(settings: "JDOSettings") -> bool:
    """Initialize Sentry error tracking and monitoring.

    Sentry is only initialized if a DSN is configured. This allows
    the application to run without Sentry for local development.

    Args:
        settings: Application settings containing Sentry configuration.

    Returns:
        True if Sentry was initialized, False otherwise.
    """
    if not settings.sentry_dsn:
        logger.debug("Sentry DSN not configured, skipping initialization")
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=f"jdo@{APP_VERSION}",
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            LoguruIntegration(
                level=logging.INFO,  # Capture INFO+ as breadcrumbs
                event_level=logging.ERROR,  # Send ERROR+ as events
            ),
        ],
        attach_stacktrace=True,
        send_default_pii=False,  # Don't send personally identifiable information
    )

    logger.info("Sentry initialized", environment=settings.environment)
    return True


def capture_exception(
    exception: Exception,
    context: dict[str, Any] | None = None,
) -> str | None:
    """Capture an exception to Sentry with optional context.

    Args:
        exception: The exception to capture.
        context: Optional dictionary of additional context.

    Returns:
        The Sentry event ID if captured, None if Sentry is not initialized.
    """
    if context:
        with sentry_sdk.push_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, value)
            return sentry_sdk.capture_exception(exception)
    return sentry_sdk.capture_exception(exception)


def add_breadcrumb(
    message: str,
    category: str = "default",
    level: str = "info",
    data: dict[str, Any] | None = None,
) -> None:
    """Add a breadcrumb for Sentry event context.

    Breadcrumbs are logged events that appear in Sentry error reports
    to help understand what happened before an error.

    Args:
        message: The breadcrumb message.
        category: Category for grouping (e.g., "ai", "database", "ui").
        level: Severity level (debug, info, warning, error, critical).
        data: Optional additional data.
    """
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=data,
    )


def set_user_context(user_id: str | None = None, email: str | None = None) -> None:
    """Set user context for Sentry events.

    Args:
        user_id: Optional user identifier.
        email: Optional user email.
    """
    if user_id or email:
        sentry_sdk.set_user({"id": user_id, "email": email})
    else:
        sentry_sdk.set_user(None)


def start_transaction(name: str, op: str = "task") -> Transaction | NoOpSpan:
    """Start a Sentry transaction for performance monitoring.

    Args:
        name: Name of the transaction (e.g., "ai_extraction").
        op: Operation type (e.g., "task", "http", "db").

    Returns:
        A Sentry Transaction or NoOpSpan that should be used as a context manager.

    Example:
        with start_transaction("extract_commitment", "ai") as txn:
            result = await extract_commitment(messages)
            txn.set_data("message_count", len(messages))
    """
    return sentry_sdk.start_transaction(name=name, op=op)


def enrich_error_context(error: Exception) -> None:
    """Enrich Sentry scope with JDOError context.

    For JDOError subclasses, this adds the recovery_hint and
    context attributes as extra data.

    Args:
        error: The exception to extract context from.
    """
    from jdo.exceptions import JDOError

    if isinstance(error, JDOError):
        sentry_sdk.set_context(
            "jdo_error",
            {
                "type": type(error).__name__,
                "message": error.message,
                "recovery_hint": error.recovery_hint,
                **error.context,
            },
        )
