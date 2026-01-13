"""Shared datetime utilities for consistent UTC handling."""

from __future__ import annotations

from datetime import UTC, date, datetime, time

DEFAULT_DUE_TIME = time(9, 0)
DEFAULT_TIMEZONE = "America/New_York"


def utc_now() -> datetime:
    """Get current UTC datetime.

    Returns:
        Current UTC datetime.
    """
    return datetime.now(UTC)


def today_date() -> date:
    """Get today's date (UTC).

    Returns:
        Today's date.
    """
    return utc_now().date()
