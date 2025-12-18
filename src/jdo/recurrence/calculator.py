"""Recurrence pattern calculator for recurring commitments."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

from jdo.models.recurring_commitment import (
    EndType,
    RecurrenceType,
    RecurringCommitment,
    RecurringCommitmentStatus,
)

# Month constants
MONTHS_IN_YEAR = 12


def get_next_due_date(
    recurring: RecurringCommitment,
    after_date: date,
) -> date | None:
    """Calculate the next due date after the given date.

    Args:
        recurring: The recurring commitment template.
        after_date: Calculate the next occurrence after this date.

    Returns:
        The next due date, or None if the recurrence has ended or is paused.
    """
    # Check if paused
    if recurring.status == RecurringCommitmentStatus.PAUSED:
        return None

    # Check end conditions
    if (
        recurring.end_type == EndType.AFTER_COUNT
        and recurring.end_after_count is not None
        and recurring.instances_generated >= recurring.end_after_count
    ):
        return None

    # Calculate next date based on pattern
    next_date = _calculate_next_date(recurring, after_date)

    if next_date is None:
        return None

    # Check if past end date
    if (
        recurring.end_type == EndType.BY_DATE
        and recurring.end_by_date is not None
        and next_date > recurring.end_by_date
    ):
        return None

    return next_date


def _calculate_next_date(
    recurring: RecurringCommitment,
    after_date: date,
) -> date | None:
    """Calculate next date based on recurrence type."""
    if recurring.recurrence_type == RecurrenceType.DAILY:
        return _calculate_daily(recurring, after_date)
    if recurring.recurrence_type == RecurrenceType.WEEKLY:
        return _calculate_weekly(recurring, after_date)
    if recurring.recurrence_type == RecurrenceType.MONTHLY:
        return _calculate_monthly(recurring, after_date)
    if recurring.recurrence_type == RecurrenceType.YEARLY:
        return _calculate_yearly(recurring, after_date)
    return None


def _calculate_daily(
    recurring: RecurringCommitment,
    after_date: date,
) -> date:
    """Calculate next date for daily recurrence."""
    return after_date + timedelta(days=recurring.interval)


def _calculate_weekly(
    recurring: RecurringCommitment,
    after_date: date,
) -> date:
    """Calculate next date for weekly recurrence.

    Args:
        recurring: The recurring commitment with days_of_week set.
        after_date: Calculate the next occurrence after this date.

    Returns:
        The next occurrence date.
    """
    if recurring.days_of_week is None:
        msg = "Weekly recurrence requires days_of_week"
        raise ValueError(msg)

    sorted_days = sorted(recurring.days_of_week)
    current_weekday = after_date.weekday()

    # Find next day in same week or next interval week
    for day in sorted_days:
        if day > current_weekday:
            # Found a day later this week
            days_ahead = day - current_weekday
            return after_date + timedelta(days=days_ahead)

    # No more days this week - go to first day of next interval week
    days_until_first = (7 - current_weekday + sorted_days[0]) % 7
    if days_until_first == 0:
        days_until_first = 7
    days_ahead = days_until_first + (recurring.interval - 1) * 7
    return after_date + timedelta(days=days_ahead)


def _calculate_monthly(
    recurring: RecurringCommitment,
    after_date: date,
) -> date:
    """Calculate next date for monthly recurrence."""
    if recurring.day_of_month is not None:
        return _calculate_monthly_by_day(recurring.day_of_month, after_date, recurring.interval)
    if recurring.week_of_month is not None and recurring.days_of_week is not None:
        return _calculate_monthly_by_week(
            recurring.week_of_month, recurring.days_of_week[0], after_date, recurring.interval
        )
    msg = "Monthly recurrence requires day_of_month or week_of_month+days_of_week"
    raise ValueError(msg)


def _calculate_monthly_by_day(
    day_of_month: int,
    after_date: date,
    interval: int = 1,
) -> date:
    """Calculate monthly recurrence by specific day of month."""
    year = after_date.year
    month = after_date.month
    target_day = day_of_month

    # Get the actual day (handle months with fewer days)
    days_in_month = calendar.monthrange(year, month)[1]
    actual_day = min(target_day, days_in_month)

    # If we're past that day this month, go to next interval month
    if after_date.day >= actual_day:
        for _ in range(interval):
            year, month = _next_month(year, month)
        days_in_month = calendar.monthrange(year, month)[1]
        actual_day = min(target_day, days_in_month)

    return date(year, month, actual_day)


def _calculate_monthly_by_week(
    week_of_month: int,
    target_weekday: int,
    after_date: date,
    interval: int = 1,
) -> date:
    """Calculate monthly recurrence by week of month and day of week."""
    # Start with current month
    year = after_date.year
    month = after_date.month

    target = _get_nth_weekday(year, month, target_weekday, week_of_month)

    # If past that date, go to next interval month
    if target <= after_date:
        for _ in range(interval):
            year, month = _next_month(year, month)
        target = _get_nth_weekday(year, month, target_weekday, week_of_month)

    return target


def _next_month(year: int, month: int) -> tuple[int, int]:
    """Return the next month and year."""
    month += 1
    if month > MONTHS_IN_YEAR:
        month = 1
        year += 1
    return year, month


def _get_nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Get the nth occurrence of a weekday in a month.

    Args:
        year: Year
        month: Month (1-12)
        weekday: Day of week (0=Monday to 6=Sunday)
        n: Which occurrence (1=first, 2=second, ..., -1=last)

    Returns:
        The date of the nth occurrence.
    """
    if n > 0:
        # Find first occurrence of weekday
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()
        days_until = (weekday - first_weekday) % 7
        first_occurrence = first_day + timedelta(days=days_until)
        # Add weeks to get to nth occurrence
        return first_occurrence + timedelta(weeks=n - 1)
    # Last occurrence: start from end of month
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    last_weekday = last_day.weekday()
    days_back = (last_weekday - weekday) % 7
    last_occurrence = last_day - timedelta(days=days_back)
    # Go back weeks for -2, -3, etc.
    return last_occurrence + timedelta(weeks=n + 1)


def _calculate_yearly(
    recurring: RecurringCommitment,
    after_date: date,
) -> date:
    """Calculate next date for yearly recurrence."""
    if recurring.month_of_year is None:
        msg = "Yearly recurrence requires month_of_year"
        raise ValueError(msg)

    if recurring.day_of_month is not None:
        return _calculate_yearly_by_day(
            recurring.month_of_year, recurring.day_of_month, after_date, recurring.interval
        )
    if recurring.week_of_month is not None and recurring.days_of_week is not None:
        return _calculate_yearly_by_week(
            recurring.month_of_year,
            recurring.week_of_month,
            recurring.days_of_week[0],
            after_date,
            recurring.interval,
        )
    msg = "Yearly recurrence requires day_of_month or week_of_month+days_of_week"
    raise ValueError(msg)


def _calculate_yearly_by_day(
    month_of_year: int,
    day_of_month: int,
    after_date: date,
    interval: int = 1,
) -> date:
    """Calculate yearly recurrence by specific month and day."""
    year = after_date.year
    month = month_of_year
    target_day = day_of_month

    # Get actual day (handle Feb 29 in non-leap years)
    days_in_month = calendar.monthrange(year, month)[1]
    actual_day = min(target_day, days_in_month)

    target = date(year, month, actual_day)

    # If past that date this year, go to next interval year
    if target <= after_date:
        year += interval
        days_in_month = calendar.monthrange(year, month)[1]
        actual_day = min(target_day, days_in_month)
        target = date(year, month, actual_day)

    return target


def _calculate_yearly_by_week(
    month_of_year: int,
    week_of_month: int,
    target_weekday: int,
    after_date: date,
    interval: int = 1,
) -> date:
    """Calculate yearly recurrence by month, week of month, and day of week."""
    year = after_date.year
    month = month_of_year

    target = _get_nth_weekday(year, month, target_weekday, week_of_month)

    # If past that date, go to next interval year
    if target <= after_date:
        year += interval
        target = _get_nth_weekday(year, month, target_weekday, week_of_month)

    return target
