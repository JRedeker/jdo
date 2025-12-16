"""Tests for natural language date/time parsing.

Phase 11: Due Date Parsing for commitments.
"""

from datetime import date, time
from unittest.mock import patch

import pytest


class TestRelativeDateParsing:
    """Tests for parsing relative date expressions."""

    def test_tomorrow_resolves_to_next_day(self) -> None:
        """'tomorrow' resolves to the next day."""
        from jdo.ai.dates import parse_date

        # Mock today as 2025-12-16 (Tuesday)
        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result = parse_date("tomorrow")

        assert result == date(2025, 12, 17)

    def test_today_resolves_to_current_day(self) -> None:
        """'today' resolves to the current day."""
        from jdo.ai.dates import parse_date

        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result = parse_date("today")

        assert result == date(2025, 12, 16)

    def test_next_friday_resolves_to_correct_date(self) -> None:
        """'next Friday' resolves to the next Friday from today."""
        from jdo.ai.dates import parse_date

        # 2025-12-16 is Tuesday, next Friday is 2025-12-19
        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result = parse_date("next Friday")

        assert result == date(2025, 12, 19)

    def test_this_friday_on_friday_returns_same_day(self) -> None:
        """'this Friday' on a Friday returns that Friday."""
        from jdo.ai.dates import parse_date

        # 2025-12-19 is Friday
        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 19)
            result = parse_date("this Friday")

        assert result == date(2025, 12, 19)

    def test_next_monday_resolves_correctly(self) -> None:
        """'next Monday' resolves to the next Monday."""
        from jdo.ai.dates import parse_date

        # 2025-12-16 is Tuesday, next Monday is 2025-12-22
        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result = parse_date("next Monday")

        assert result == date(2025, 12, 22)


class TestAbsoluteDateParsing:
    """Tests for parsing absolute date expressions."""

    def test_december_20_resolves_to_specific_date(self) -> None:
        """'December 20' resolves to that date in the current/next year."""
        from jdo.ai.dates import parse_date

        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result = parse_date("December 20")

        assert result == date(2025, 12, 20)

    def test_december_20th_with_ordinal(self) -> None:
        """'December 20th' with ordinal suffix works."""
        from jdo.ai.dates import parse_date

        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result = parse_date("December 20th")

        assert result == date(2025, 12, 20)

    def test_dec_20_short_month(self) -> None:
        """'Dec 20' with abbreviated month works."""
        from jdo.ai.dates import parse_date

        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result = parse_date("Dec 20")

        assert result == date(2025, 12, 20)

    def test_past_date_rolls_to_next_year(self) -> None:
        """Date that has passed this year rolls to next year."""
        from jdo.ai.dates import parse_date

        # Today is December 16, January 5 means next year
        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result = parse_date("January 5")

        assert result == date(2026, 1, 5)

    def test_iso_date_format(self) -> None:
        """'2025-12-25' ISO format works."""
        from jdo.ai.dates import parse_date

        result = parse_date("2025-12-25")

        assert result == date(2025, 12, 25)

    def test_slash_date_format(self) -> None:
        """'12/25/2025' US format works."""
        from jdo.ai.dates import parse_date

        result = parse_date("12/25/2025")

        assert result == date(2025, 12, 25)


class TestTimeParsing:
    """Tests for parsing time expressions."""

    def test_3pm_sets_time_to_15_00(self) -> None:
        """'3pm' sets due_time to 15:00."""
        from jdo.ai.dates import parse_time

        result = parse_time("3pm")

        assert result == time(15, 0)

    def test_3_pm_with_space(self) -> None:
        """'3 pm' with space works."""
        from jdo.ai.dates import parse_time

        result = parse_time("3 pm")

        assert result == time(15, 0)

    def test_15_00_24hour(self) -> None:
        """'15:00' 24-hour format works."""
        from jdo.ai.dates import parse_time

        result = parse_time("15:00")

        assert result == time(15, 0)

    def test_3_30pm_with_minutes(self) -> None:
        """'3:30pm' with minutes works."""
        from jdo.ai.dates import parse_time

        result = parse_time("3:30pm")

        assert result == time(15, 30)

    def test_end_of_day_sets_17_00(self) -> None:
        """'end of day' sets due_time to 17:00."""
        from jdo.ai.dates import parse_time

        result = parse_time("end of day")

        assert result == time(17, 0)

    def test_eod_abbreviation(self) -> None:
        """'EOD' abbreviation sets due_time to 17:00."""
        from jdo.ai.dates import parse_time

        result = parse_time("EOD")

        assert result == time(17, 0)

    def test_noon_sets_12_00(self) -> None:
        """'noon' sets due_time to 12:00."""
        from jdo.ai.dates import parse_time

        result = parse_time("noon")

        assert result == time(12, 0)

    def test_midnight_sets_00_00(self) -> None:
        """'midnight' sets due_time to 00:00."""
        from jdo.ai.dates import parse_time

        result = parse_time("midnight")

        assert result == time(0, 0)


class TestVagueDateRejection:
    """Tests for rejecting vague date expressions."""

    def test_next_week_rejected_as_too_vague(self) -> None:
        """'next week' is rejected as too vague."""
        from jdo.ai.dates import VagueDateError, parse_date

        with pytest.raises(VagueDateError, match="too vague"):
            parse_date("next week")

    def test_soon_rejected_as_too_vague(self) -> None:
        """'soon' is rejected as too vague."""
        from jdo.ai.dates import VagueDateError, parse_date

        with pytest.raises(VagueDateError, match="too vague"):
            parse_date("soon")

    def test_later_rejected_as_too_vague(self) -> None:
        """'later' is rejected as too vague."""
        from jdo.ai.dates import VagueDateError, parse_date

        with pytest.raises(VagueDateError, match="too vague"):
            parse_date("later")

    def test_asap_rejected_as_too_vague(self) -> None:
        """'ASAP' is rejected as too vague."""
        from jdo.ai.dates import VagueDateError, parse_date

        with pytest.raises(VagueDateError, match="too vague"):
            parse_date("ASAP")


class TestDefaultTime:
    """Tests for default time when not specified."""

    def test_date_without_time_defaults_to_09_00(self) -> None:
        """Date without time defaults to 09:00."""
        from jdo.ai.dates import parse_datetime

        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result_date, result_time = parse_datetime("tomorrow")

        assert result_date == date(2025, 12, 17)
        assert result_time == time(9, 0)

    def test_date_with_time_uses_specified_time(self) -> None:
        """Date with time uses the specified time."""
        from jdo.ai.dates import parse_datetime

        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result_date, result_time = parse_datetime("tomorrow at 3pm")

        assert result_date == date(2025, 12, 17)
        assert result_time == time(15, 0)

    def test_date_with_by_time(self) -> None:
        """'by 5pm' extracts the time correctly."""
        from jdo.ai.dates import parse_datetime

        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 12, 16)
            result_date, result_time = parse_datetime("December 20 by 5pm")

        assert result_date == date(2025, 12, 20)
        assert result_time == time(17, 0)


class TestInvalidInput:
    """Tests for handling invalid input."""

    def test_unparseable_date_raises_error(self) -> None:
        """Unparseable date raises ParseError."""
        from jdo.ai.dates import ParseError, parse_date

        with pytest.raises(ParseError):
            parse_date("xyzzy")

    def test_empty_string_raises_error(self) -> None:
        """Empty string raises ParseError."""
        from jdo.ai.dates import ParseError, parse_date

        with pytest.raises(ParseError):
            parse_date("")

    def test_unparseable_time_raises_error(self) -> None:
        """Unparseable time raises ParseError."""
        from jdo.ai.dates import ParseError, parse_time

        with pytest.raises(ParseError):
            parse_time("xyzzy")
