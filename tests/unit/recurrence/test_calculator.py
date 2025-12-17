"""Tests for recurrence calculator - TDD Red phase."""

from datetime import date
from uuid import uuid4

import pytest

from jdo.models.recurring_commitment import RecurrenceType, RecurringCommitment


class TestDailyPattern:
    """Tests for daily recurrence pattern."""

    def test_daily_returns_next_day(self) -> None:
        """Daily pattern returns next day after reference date."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Daily standup",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        # Reference date is Monday Dec 16, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 16))

        # Next occurrence is Dec 17, 2025
        assert result == date(2025, 12, 17)

    def test_daily_with_interval_2_returns_every_other_day(self) -> None:
        """Daily pattern with interval=2 returns every other day."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Biweekly task",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            interval=2,
        )

        # Reference date is Monday Dec 16, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 16))

        # Next occurrence is Dec 18, 2025 (2 days later)
        assert result == date(2025, 12, 18)

    def test_daily_with_interval_7_returns_weekly(self) -> None:
        """Daily pattern with interval=7 returns weekly."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Weekly via daily",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            interval=7,
        )

        result = get_next_due_date(recurring, after_date=date(2025, 12, 16))
        assert result == date(2025, 12, 23)


class TestWeeklyPattern:
    """Tests for weekly recurrence pattern."""

    def test_weekly_on_monday_returns_next_monday(self) -> None:
        """Weekly on Monday returns next Monday."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Weekly report",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],  # Monday
        )

        # Reference is Tuesday Dec 17, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 17))

        # Next Monday is Dec 22, 2025
        assert result == date(2025, 12, 22)

    def test_weekly_on_monday_from_monday_returns_next_week_monday(self) -> None:
        """Weekly on Monday from a Monday returns the following Monday."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Weekly report",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],  # Monday
        )

        # Reference is Monday Dec 15, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 15))

        # Next Monday is Dec 22, 2025
        assert result == date(2025, 12, 22)

    def test_weekly_on_mon_wed_fri_returns_nearest(self) -> None:
        """Weekly on Mon, Wed, Fri returns nearest future day."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="MWF task",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0, 2, 4],  # Mon, Wed, Fri
        )

        # Reference is Tuesday Dec 16, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 16))

        # Next is Wednesday Dec 17, 2025
        assert result == date(2025, 12, 17)

    def test_weekly_with_interval_2_returns_every_other_week(self) -> None:
        """Weekly with interval=2 returns every other week."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Biweekly report",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],  # Monday
            interval=2,
        )

        # Reference is Monday Dec 15, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 15))

        # Next occurrence is Monday Dec 29, 2025 (2 weeks later)
        assert result == date(2025, 12, 29)


class TestMonthlyPattern:
    """Tests for monthly recurrence pattern."""

    def test_monthly_on_15th_returns_next_15th(self) -> None:
        """Monthly on 15th returns next 15th."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Monthly report",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            day_of_month=15,
        )

        # Reference is Dec 10, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 10))

        # Next 15th is Dec 15, 2025
        assert result == date(2025, 12, 15)

    def test_monthly_on_15th_from_15th_returns_next_month(self) -> None:
        """Monthly on 15th from 15th returns next month's 15th."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Monthly report",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            day_of_month=15,
        )

        # Reference is Dec 15, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 15))

        # Next 15th is Jan 15, 2026
        assert result == date(2026, 1, 15)

    def test_monthly_on_31st_uses_last_day_for_short_months(self) -> None:
        """Monthly on 31st uses last day for months with fewer days."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="End of month",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            day_of_month=31,
        )

        # Reference is Jan 31, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 1, 31))

        # February 2025 has 28 days, so should be Feb 28
        assert result == date(2025, 2, 28)

    def test_monthly_2nd_friday_returns_correct_date(self) -> None:
        """Monthly on 2nd Friday returns correct date."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="2nd Friday meeting",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            week_of_month=2,
            days_of_week=[4],  # Friday
        )

        # Reference is Dec 1, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 1))

        # 2nd Friday of Dec 2025 is Dec 12
        assert result == date(2025, 12, 12)

    def test_monthly_last_friday_returns_correct_date(self) -> None:
        """Monthly on last Friday returns correct date."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Last Friday review",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            week_of_month=-1,  # Last week
            days_of_week=[4],  # Friday
        )

        # Reference is Dec 1, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 12, 1))

        # Last Friday of Dec 2025 is Dec 26
        assert result == date(2025, 12, 26)


class TestYearlyPattern:
    """Tests for yearly recurrence pattern."""

    def test_yearly_march_15_returns_next_occurrence(self) -> None:
        """Yearly on March 15 returns next occurrence."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Annual review",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.YEARLY,
            month_of_year=3,  # March
            day_of_month=15,
        )

        # Reference is Feb 1, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 2, 1))

        # Next March 15 is 2025
        assert result == date(2025, 3, 15)

    def test_yearly_after_date_returns_next_year(self) -> None:
        """Yearly pattern after the date returns next year."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Annual review",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.YEARLY,
            month_of_year=3,  # March
            day_of_month=15,
        )

        # Reference is March 20, 2025
        result = get_next_due_date(recurring, after_date=date(2025, 3, 20))

        # Next March 15 is 2026
        assert result == date(2026, 3, 15)

    def test_yearly_feb_29_handles_non_leap_years(self) -> None:
        """Yearly on Feb 29 handles non-leap years (uses Feb 28)."""
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Leap day task",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.YEARLY,
            month_of_year=2,  # February
            day_of_month=29,
        )

        # Reference is Jan 1, 2025 (2025 is not a leap year)
        result = get_next_due_date(recurring, after_date=date(2025, 1, 1))

        # Feb 29, 2025 doesn't exist, should use Feb 28
        assert result == date(2025, 2, 28)


class TestEndConditions:
    """Tests for end condition handling."""

    def test_returns_none_when_after_count_reached(self) -> None:
        """Returns None when instances_generated >= end_after_count."""
        from jdo.models.recurring_commitment import EndType
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Limited task",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.AFTER_COUNT,
            end_after_count=5,
            instances_generated=5,
        )

        result = get_next_due_date(recurring, after_date=date(2025, 12, 16))
        assert result is None

    def test_returns_none_when_past_end_date(self) -> None:
        """Returns None when next due date would be past end_by_date."""
        from jdo.models.recurring_commitment import EndType
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Limited task",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.BY_DATE,
            end_by_date=date(2025, 12, 17),
        )

        # Reference date is Dec 17, so next would be Dec 18
        result = get_next_due_date(recurring, after_date=date(2025, 12, 17))
        assert result is None

    def test_continues_with_end_type_never(self) -> None:
        """Continues generating with end_type=never."""
        from jdo.models.recurring_commitment import EndType
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Forever task",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            end_type=EndType.NEVER,
            instances_generated=1000,  # Many instances
        )

        result = get_next_due_date(recurring, after_date=date(2025, 12, 16))
        assert result == date(2025, 12, 17)

    def test_paused_recurrence_returns_none(self) -> None:
        """Paused recurrence returns None."""
        from jdo.models.recurring_commitment import RecurringCommitmentStatus
        from jdo.recurrence.calculator import get_next_due_date

        recurring = RecurringCommitment(
            deliverable_template="Paused task",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            status=RecurringCommitmentStatus.PAUSED,
        )

        result = get_next_due_date(recurring, after_date=date(2025, 12, 16))
        assert result is None
