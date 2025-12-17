"""Tests for pattern summary formatter - TDD Red phase."""

from uuid import uuid4

import pytest

from jdo.models.recurring_commitment import (
    EndType,
    RecurrenceType,
    RecurringCommitment,
)


class TestFormatPatternSummary:
    """Tests for format_pattern_summary function."""

    def test_daily_pattern(self) -> None:
        """Daily pattern shows 'Daily'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
        )

        result = format_pattern_summary(recurring)

        assert result == "Daily"

    def test_daily_pattern_with_interval(self) -> None:
        """Daily pattern with interval shows 'Every N days'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.DAILY,
            interval=3,
        )

        result = format_pattern_summary(recurring)

        assert result == "Every 3 days"

    def test_weekly_single_day(self) -> None:
        """Weekly on single day shows 'Weekly on Mon'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],  # Monday
        )

        result = format_pattern_summary(recurring)

        assert result == "Weekly on Mon"

    def test_weekly_multiple_days(self) -> None:
        """Weekly on multiple days shows 'Weekly on Mon, Wed, Fri'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0, 2, 4],  # Mon, Wed, Fri
        )

        result = format_pattern_summary(recurring)

        assert result == "Weekly on Mon, Wed, Fri"

    def test_weekly_with_interval(self) -> None:
        """Weekly with interval shows 'Every 2 weeks on Mon'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.WEEKLY,
            days_of_week=[0],
            interval=2,
        )

        result = format_pattern_summary(recurring)

        assert result == "Every 2 weeks on Mon"

    def test_monthly_day_of_month(self) -> None:
        """Monthly on day shows 'Monthly on the 15th'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            day_of_month=15,
        )

        result = format_pattern_summary(recurring)

        assert result == "Monthly on the 15th"

    def test_monthly_first_of_month(self) -> None:
        """Monthly on 1st shows 'Monthly on the 1st'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            day_of_month=1,
        )

        result = format_pattern_summary(recurring)

        assert result == "Monthly on the 1st"

    def test_monthly_second_of_month(self) -> None:
        """Monthly on 2nd shows 'Monthly on the 2nd'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            day_of_month=2,
        )

        result = format_pattern_summary(recurring)

        assert result == "Monthly on the 2nd"

    def test_monthly_third_of_month(self) -> None:
        """Monthly on 3rd shows 'Monthly on the 3rd'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            day_of_month=3,
        )

        result = format_pattern_summary(recurring)

        assert result == "Monthly on the 3rd"

    def test_monthly_week_of_month(self) -> None:
        """Monthly on 2nd Tuesday shows 'Monthly on the 2nd Tue'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            week_of_month=2,
            days_of_week=[1],  # Tuesday
        )

        result = format_pattern_summary(recurring)

        assert result == "Monthly on the 2nd Tue"

    def test_monthly_last_friday(self) -> None:
        """Monthly on last Friday shows 'Monthly on the last Fri'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            week_of_month=5,  # 5 = last
            days_of_week=[4],  # Friday
        )

        result = format_pattern_summary(recurring)

        assert result == "Monthly on the last Fri"

    def test_monthly_with_interval(self) -> None:
        """Monthly with interval shows 'Every 3 months on the 15th'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.MONTHLY,
            day_of_month=15,
            interval=3,
        )

        result = format_pattern_summary(recurring)

        assert result == "Every 3 months on the 15th"

    def test_yearly_pattern(self) -> None:
        """Yearly shows 'Yearly on Mar 15'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.YEARLY,
            month_of_year=3,
            day_of_month=15,
        )

        result = format_pattern_summary(recurring)

        assert result == "Yearly on Mar 15"

    def test_yearly_with_interval(self) -> None:
        """Yearly with interval shows 'Every 2 years on Mar 15'."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.YEARLY,
            month_of_year=3,
            day_of_month=15,
            interval=2,
        )

        result = format_pattern_summary(recurring)

        assert result == "Every 2 years on Mar 15"

    def test_yearly_week_pattern(self) -> None:
        """Yearly on 3rd Monday of June shows correct pattern."""
        from jdo.recurrence.formatter import format_pattern_summary

        recurring = RecurringCommitment(
            deliverable_template="Test",
            stakeholder_id=uuid4(),
            recurrence_type=RecurrenceType.YEARLY,
            month_of_year=6,
            week_of_month=3,
            days_of_week=[0],  # Monday
        )

        result = format_pattern_summary(recurring)

        assert result == "Yearly on the 3rd Mon of Jun"


class TestOrdinalSuffix:
    """Tests for ordinal suffix helper."""

    def test_first(self) -> None:
        """1 returns 1st."""
        from jdo.recurrence.formatter import ordinal_suffix

        assert ordinal_suffix(1) == "1st"

    def test_second(self) -> None:
        """2 returns 2nd."""
        from jdo.recurrence.formatter import ordinal_suffix

        assert ordinal_suffix(2) == "2nd"

    def test_third(self) -> None:
        """3 returns 3rd."""
        from jdo.recurrence.formatter import ordinal_suffix

        assert ordinal_suffix(3) == "3rd"

    def test_fourth(self) -> None:
        """4 returns 4th."""
        from jdo.recurrence.formatter import ordinal_suffix

        assert ordinal_suffix(4) == "4th"

    def test_eleventh(self) -> None:
        """11 returns 11th (special case)."""
        from jdo.recurrence.formatter import ordinal_suffix

        assert ordinal_suffix(11) == "11th"

    def test_twelfth(self) -> None:
        """12 returns 12th (special case)."""
        from jdo.recurrence.formatter import ordinal_suffix

        assert ordinal_suffix(12) == "12th"

    def test_thirteenth(self) -> None:
        """13 returns 13th (special case)."""
        from jdo.recurrence.formatter import ordinal_suffix

        assert ordinal_suffix(13) == "13th"

    def test_twenty_first(self) -> None:
        """21 returns 21st."""
        from jdo.recurrence.formatter import ordinal_suffix

        assert ordinal_suffix(21) == "21st"

    def test_thirty_first(self) -> None:
        """31 returns 31st."""
        from jdo.recurrence.formatter import ordinal_suffix

        assert ordinal_suffix(31) == "31st"
