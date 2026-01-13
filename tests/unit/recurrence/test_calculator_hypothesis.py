"""Property-based tests for recurrence pattern calculator using hypothesis.

These tests verify that recurrence calculations produce valid dates
and maintain expected properties across various inputs.
"""

from datetime import date, timedelta

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from jdo.models.recurring_commitment import (
    EndType,
    RecurrenceType,
    RecurringCommitment,
    RecurringCommitmentStatus,
)

# Strategy for generating valid dates
valid_dates = st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 12, 31))


class TestGetNextDueDateProperties:
    """Property-based tests for get_next_due_date function."""

    @given(valid_dates, st.integers(min_value=1, max_value=7))
    @settings(max_examples=50)
    def test_daily_recurrence_advances_by_interval(self, after_date: date, interval: int) -> None:
        """Daily recurrence should advance by the specified interval."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Test daily",
            stakeholder_name="Test",
            recurrence_type=RecurrenceType.DAILY,
            interval=interval,
            start_date=after_date - timedelta(days=100),  # Started well before
        )

        result = get_next_due_date(recurring, after_date)

        assert result is not None
        # Result should be after the given date
        assert result > after_date
        # Result should be at most interval days after after_date
        assert result <= after_date + timedelta(days=interval)

    @given(
        valid_dates, st.integers(min_value=1, max_value=4), st.integers(min_value=0, max_value=6)
    )
    @settings(max_examples=50)
    def test_weekly_recurrence_advances_by_weeks(
        self, after_date: date, interval: int, day_of_week: int
    ) -> None:
        """Weekly recurrence should advance by weeks."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Test weekly",
            stakeholder_name="Test",
            recurrence_type=RecurrenceType.WEEKLY,
            interval=interval,
            start_date=after_date - timedelta(days=100),
            days_of_week=[day_of_week],  # Required for weekly recurrence
        )

        result = get_next_due_date(recurring, after_date)

        assert result is not None
        assert result > after_date
        # Should be within interval weeks (plus buffer for day alignment)
        assert result <= after_date + timedelta(weeks=interval + 1)

    @given(
        valid_dates, st.integers(min_value=1, max_value=6), st.integers(min_value=1, max_value=28)
    )
    @settings(max_examples=50)
    def test_monthly_recurrence_stays_in_valid_range(
        self, after_date: date, interval: int, day_of_month: int
    ) -> None:
        """Monthly recurrence should produce valid dates."""
        from jdo.recurrence.calculator import get_next_due_date

        # Use a safe start day that exists in all months
        safe_start = date(after_date.year - 1, after_date.month, min(after_date.day, 28))

        recurring = RecurringCommitment(
            deliverable_template="Test monthly",
            stakeholder_name="Test",
            recurrence_type=RecurrenceType.MONTHLY,
            interval=interval,
            start_date=safe_start,
            day_of_month=day_of_month,  # Required for monthly recurrence
        )

        result = get_next_due_date(recurring, after_date)

        if result is not None:
            assert result > after_date
            # Result should be a valid date (no exception from date creation)
            assert 1 <= result.day <= 31
            assert 1 <= result.month <= 12

    @given(valid_dates, st.integers(min_value=1, max_value=12))
    @settings(max_examples=30)
    def test_yearly_recurrence_advances_by_years(
        self, after_date: date, month_of_year: int
    ) -> None:
        """Yearly recurrence should advance by approximately one year."""
        from jdo.recurrence.calculator import get_next_due_date

        # Avoid Feb 29 to prevent leap year complications
        assume(not (after_date.month == 2 and after_date.day == 29))

        recurring = RecurringCommitment(
            deliverable_template="Test yearly",
            stakeholder_name="Test",
            recurrence_type=RecurrenceType.YEARLY,
            interval=1,
            start_date=after_date - timedelta(days=400),  # Started over a year ago
            month_of_year=month_of_year,  # Required for yearly recurrence
            day_of_month=15,  # Use a safe day that exists in all months
        )

        result = get_next_due_date(recurring, after_date)

        if result is not None:
            assert result > after_date
            # Should be roughly within a year
            assert result <= after_date + timedelta(days=366)


class TestRecurrenceEndConditions:
    """Property-based tests for recurrence end conditions."""

    @given(valid_dates, st.integers(min_value=1, max_value=10))
    @settings(max_examples=30)
    def test_end_after_count_respects_limit(self, after_date: date, max_count: int) -> None:
        """Recurrence with end_after_count should stop after the limit."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Test limited",
            stakeholder_name="Test",
            recurrence_type=RecurrenceType.DAILY,
            interval=1,
            start_date=after_date - timedelta(days=100),
            end_type=EndType.AFTER_COUNT,
            end_after_count=max_count,
            instances_generated=max_count,  # Already at limit
        )

        result = get_next_due_date(recurring, after_date)

        # Should return None when limit is reached
        assert result is None

    @given(valid_dates, valid_dates)
    @settings(max_examples=30)
    def test_end_by_date_respects_deadline(self, after_date: date, end_date: date) -> None:
        """Recurrence with end_by_date should not go past the deadline."""
        from jdo.recurrence.calculator import get_next_due_date

        # End date must be before or equal to after_date for meaningful test
        assume(end_date <= after_date)

        recurring = RecurringCommitment(
            deliverable_template="Test deadline",
            stakeholder_name="Test",
            recurrence_type=RecurrenceType.DAILY,
            interval=1,
            start_date=end_date - timedelta(days=100),
            end_type=EndType.BY_DATE,
            end_by_date=end_date,
        )

        result = get_next_due_date(recurring, after_date)

        # Should return None when past end date
        assert result is None

    @given(valid_dates)
    @settings(max_examples=20)
    def test_paused_recurrence_returns_none(self, after_date: date) -> None:
        """Paused recurrence should always return None."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Test paused",
            stakeholder_name="Test",
            recurrence_type=RecurrenceType.DAILY,
            interval=1,
            start_date=after_date - timedelta(days=100),
            status=RecurringCommitmentStatus.PAUSED,
        )

        result = get_next_due_date(recurring, after_date)

        assert result is None


class TestRecurrenceMonotonicity:
    """Property-based tests ensuring recurrence dates are monotonically increasing."""

    @given(valid_dates, st.integers(min_value=1, max_value=3))
    @settings(max_examples=30)
    def test_consecutive_dates_are_increasing(self, start: date, interval: int) -> None:
        """Consecutive recurrence dates should always increase (daily only)."""
        from jdo.recurrence.calculator import get_next_due_date

        # Only test daily recurrence since it doesn't require additional fields
        recurring = RecurringCommitment(
            deliverable_template="Test monotonic",
            stakeholder_name="Test",
            recurrence_type=RecurrenceType.DAILY,
            interval=interval,
            start_date=start,
        )

        # Get first date
        date1 = get_next_due_date(recurring, start)
        assume(date1 is not None)

        # Get second date (after first)
        date2 = get_next_due_date(recurring, date1)

        if date2 is not None:
            assert date2 > date1, "Second date should be after first date"


class TestRecurrenceIntervalProperties:
    """Property-based tests for interval behavior."""

    @given(st.integers(min_value=1, max_value=30))
    @settings(max_examples=30)
    def test_daily_interval_gap_is_correct(self, interval: int) -> None:
        """Daily recurrence gap should equal the interval."""
        from jdo.recurrence.calculator import get_next_due_date

        start = date(2025, 6, 15)
        recurring = RecurringCommitment(
            deliverable_template="Test interval",
            stakeholder_name="Test",
            recurrence_type=RecurrenceType.DAILY,
            interval=interval,
            start_date=start,
        )

        # Get consecutive dates
        date1 = get_next_due_date(recurring, start)
        assert date1 is not None

        date2 = get_next_due_date(recurring, date1)
        assert date2 is not None

        # Gap should be exactly interval days
        assert (date2 - date1).days == interval
