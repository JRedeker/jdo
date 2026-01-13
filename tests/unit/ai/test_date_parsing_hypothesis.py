"""Property-based tests for date/time parsing using hypothesis.

These tests verify that the date parser handles arbitrary input safely
and produces consistent results for known-good patterns.
"""

from datetime import date, time

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st


class TestDateParsingRobustness:
    """Property-based tests ensuring date parser never crashes on arbitrary input."""

    @given(st.text(max_size=200))
    @settings(max_examples=100)
    def test_parse_date_never_crashes_on_arbitrary_input(self, text: str) -> None:
        """parse_date should handle any string without crashing."""
        from jdo.ai.dates import ParseError, VagueDateError, parse_date

        # parse_date should either return a date or raise ParseError/VagueDateError
        # It should NEVER raise any other exception
        try:
            result = parse_date(text)
            # If we got a result, it must be a date
            assert isinstance(result, date)
        except (ParseError, VagueDateError):
            pass  # Expected for invalid/vague input

    @given(st.text(max_size=200))
    @settings(max_examples=100)
    def test_parse_time_never_crashes_on_arbitrary_input(self, text: str) -> None:
        """parse_time should handle any string without crashing."""
        from jdo.ai.dates import ParseError, parse_time

        try:
            result = parse_time(text)
            assert isinstance(result, time)
        except ParseError:
            pass  # Expected for invalid input

    @given(st.text(max_size=200))
    @settings(max_examples=100)
    def test_parse_datetime_never_crashes_on_arbitrary_input(self, text: str) -> None:
        """parse_datetime should handle any string without crashing."""
        from jdo.ai.dates import ParseError, VagueDateError, parse_datetime

        try:
            result_date, result_time = parse_datetime(text)
            assert isinstance(result_date, date)
            assert isinstance(result_time, time)
        except (ParseError, VagueDateError):
            pass  # Expected for invalid/vague input


class TestDateParsingConsistency:
    """Property-based tests ensuring consistent parsing behavior."""

    @given(st.integers(min_value=1, max_value=12), st.integers(min_value=1, max_value=28))
    @settings(max_examples=50)
    def test_month_day_combinations_parse_consistently(self, month: int, day: int) -> None:
        """Valid month/day combinations should parse consistently."""
        from unittest.mock import patch

        from jdo.ai.dates import parse_date

        months = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        month_name = months[month - 1]

        # Mock today to a consistent date
        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 1, 1)
            result = parse_date(f"{month_name} {day}")

        assert result.month == month
        assert result.day == day

    @given(st.integers(min_value=1, max_value=12), st.integers(min_value=0, max_value=59))
    @settings(max_examples=50)
    def test_time_parsing_consistency(self, hour: int, minute: int) -> None:
        """Valid hour:minute combinations should parse consistently."""
        from jdo.ai.dates import parse_time

        # Test 12-hour format (1-12 with am/pm)
        if hour == 0:
            hour_12 = 12
            period = "am"
            expected_hour = 0
        elif hour < 12:
            hour_12 = hour
            period = "am"
            expected_hour = hour
        elif hour == 12:
            hour_12 = 12
            period = "pm"
            expected_hour = 12
        else:
            hour_12 = hour - 12
            period = "pm"
            expected_hour = hour

        # Skip hour=0 for 12-hour format as it's represented as 12am
        assume(hour != 0 or (hour == 0 and minute == 0))

        time_str = f"{hour_12}:{minute:02d}{period}"
        result = parse_time(time_str)

        assert result.hour == expected_hour
        assert result.minute == minute

    @given(
        st.sampled_from(
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        )
    )
    @settings(max_examples=20)
    def test_day_of_week_parsing(self, day_name: str) -> None:
        """Day names should always parse to valid dates."""
        from unittest.mock import patch

        from jdo.ai.dates import parse_date

        with patch("jdo.ai.dates.today_date") as mock_today:
            mock_today.return_value = date(2025, 1, 6)  # Monday
            result = parse_date(f"next {day_name}")

        assert isinstance(result, date)
        # Result should be within 7 days of the mocked today
        assert result > date(2025, 1, 6)
        assert result <= date(2025, 1, 13)


class TestTimeEdgeCases:
    """Property-based tests for time parsing edge cases."""

    @given(st.integers(min_value=0, max_value=23))
    @settings(max_examples=24)
    def test_24_hour_format_all_hours(self, hour: int) -> None:
        """All valid 24-hour format times should parse correctly."""
        from jdo.ai.dates import parse_time

        time_str = f"{hour:02d}:00"
        result = parse_time(time_str)

        assert result.hour == hour
        assert result.minute == 0

    @given(st.sampled_from(["noon", "midnight", "eod", "end of day"]))
    @settings(max_examples=10)
    def test_named_times_always_parse(self, named_time: str) -> None:
        """Named times should always parse to expected values."""
        from jdo.ai.dates import parse_time

        expected = {
            "noon": time(12, 0),
            "midnight": time(0, 0),
            "eod": time(17, 0),
            "end of day": time(17, 0),
        }

        result = parse_time(named_time)
        assert result == expected[named_time]


class TestISODateFormats:
    """Property-based tests for ISO date format parsing."""

    @given(
        st.integers(min_value=2020, max_value=2030),
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
    )
    @settings(max_examples=50)
    def test_iso_format_parses_correctly(self, year: int, month: int, day: int) -> None:
        """ISO format dates should parse to correct date objects."""
        from jdo.ai.dates import parse_date

        iso_str = f"{year}-{month:02d}-{day:02d}"
        result = parse_date(iso_str)

        assert result == date(year, month, day)

    @given(
        st.integers(min_value=1, max_value=12),
        st.integers(min_value=1, max_value=28),
        st.integers(min_value=2020, max_value=2030),
    )
    @settings(max_examples=50)
    def test_us_slash_format_parses_correctly(self, month: int, day: int, year: int) -> None:
        """US slash format dates should parse to correct date objects."""
        from jdo.ai.dates import parse_date

        slash_str = f"{month}/{day}/{year}"
        result = parse_date(slash_str)

        assert result == date(year, month, day)
