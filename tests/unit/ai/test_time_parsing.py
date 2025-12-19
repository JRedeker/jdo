"""Tests for natural language time parsing."""

from __future__ import annotations

import pytest

from jdo.ai.time_parsing import (
    ParsedTime,
    format_hours,
    parse_time_input,
    round_to_increment,
)


class TestRoundToIncrement:
    """Tests for round_to_increment function."""

    def test_rounds_up_to_quarter_hour(self) -> None:
        """round_to_increment rounds up to 15-minute increments."""
        assert round_to_increment(0.1) == 0.25
        assert round_to_increment(0.26) == 0.5
        assert round_to_increment(0.51) == 0.75
        assert round_to_increment(0.76) == 1.0

    def test_exact_increments_unchanged(self) -> None:
        """Exact 15-minute increments are unchanged."""
        assert round_to_increment(0.25) == 0.25
        assert round_to_increment(0.5) == 0.5
        assert round_to_increment(0.75) == 0.75
        assert round_to_increment(1.0) == 1.0
        assert round_to_increment(1.5) == 1.5
        assert round_to_increment(2.0) == 2.0

    def test_zero_unchanged(self) -> None:
        """Zero returns zero."""
        assert round_to_increment(0.0) == 0.0

    def test_negative_returns_zero(self) -> None:
        """Negative values return zero."""
        assert round_to_increment(-1.0) == 0.0


class TestParseTimeInputHours:
    """Tests for parsing hour-based time inputs."""

    def test_parses_hours_word(self) -> None:
        """Parses 'X hours' format."""
        result = parse_time_input("2 hours")
        assert result is not None
        assert result.hours == 2.0
        assert result.confidence == 1.0

    def test_parses_hour_singular(self) -> None:
        """Parses 'X hour' format."""
        result = parse_time_input("1 hour")
        assert result is not None
        assert result.hours == 1.0

    def test_parses_hrs_abbreviation(self) -> None:
        """Parses 'X hrs' format."""
        result = parse_time_input("3 hrs")
        assert result is not None
        assert result.hours == 3.0

    def test_parses_h_suffix(self) -> None:
        """Parses 'Xh' format."""
        result = parse_time_input("4h")
        assert result is not None
        assert result.hours == 4.0

    def test_parses_decimal_hours(self) -> None:
        """Parses '1.5 hours' format."""
        result = parse_time_input("1.5 hours")
        assert result is not None
        assert result.hours == 1.5

    def test_parses_decimal_h(self) -> None:
        """Parses '2.5h' format."""
        result = parse_time_input("2.5h")
        assert result is not None
        assert result.hours == 2.5

    def test_rounds_hours_up(self) -> None:
        """Rounds hours up to 15-minute increments."""
        result = parse_time_input("1.1h")
        assert result is not None
        assert result.hours == 1.25  # Rounded up


class TestParseTimeInputMinutes:
    """Tests for parsing minute-based time inputs."""

    def test_parses_minutes_word(self) -> None:
        """Parses 'X minutes' format."""
        result = parse_time_input("30 minutes")
        assert result is not None
        assert result.hours == 0.5

    def test_parses_minute_singular(self) -> None:
        """Parses 'X minute' format."""
        result = parse_time_input("15 minute")
        assert result is not None
        assert result.hours == 0.25

    def test_parses_mins_abbreviation(self) -> None:
        """Parses 'X mins' format."""
        result = parse_time_input("45 mins")
        assert result is not None
        assert result.hours == 0.75

    def test_parses_min_abbreviation(self) -> None:
        """Parses 'X min' format."""
        result = parse_time_input("60 min")
        assert result is not None
        assert result.hours == 1.0

    def test_parses_m_suffix(self) -> None:
        """Parses 'Xm' format."""
        result = parse_time_input("90m")
        assert result is not None
        assert result.hours == 1.5

    def test_rounds_minutes_up(self) -> None:
        """Rounds minutes up to 15-minute increments."""
        result = parse_time_input("20 min")
        assert result is not None
        assert result.hours == 0.5  # 20 minutes rounds up to 30 (0.5h)


class TestParseTimeInputColonFormat:
    """Tests for parsing hours:minutes format."""

    def test_parses_colon_format(self) -> None:
        """Parses 'H:MM' format."""
        result = parse_time_input("1:30")
        assert result is not None
        assert result.hours == 1.5

    def test_parses_zero_hours(self) -> None:
        """Parses '0:30' format."""
        result = parse_time_input("0:30")
        assert result is not None
        assert result.hours == 0.5

    def test_parses_long_hours(self) -> None:
        """Parses '10:00' format."""
        result = parse_time_input("10:00")
        assert result is not None
        assert result.hours == 10.0

    def test_rounds_colon_format_up(self) -> None:
        """Rounds colon format up to 15-minute increments."""
        result = parse_time_input("1:10")
        assert result is not None
        assert result.hours == 1.25  # 1:10 (1.167h) rounds up to 1.25


class TestParseTimeInputPlainNumbers:
    """Tests for parsing plain numbers."""

    def test_small_numbers_as_hours(self) -> None:
        """Small numbers (<12) are treated as hours."""
        result = parse_time_input("2")
        assert result is not None
        assert result.hours == 2.0
        assert result.confidence < 1.0  # Lower confidence

    def test_medium_numbers_as_minutes(self) -> None:
        """Medium numbers (12-60) are treated as minutes."""
        result = parse_time_input("30")
        assert result is not None
        assert result.hours == 0.5
        assert result.confidence < 1.0

    def test_large_numbers_as_minutes(self) -> None:
        """Large numbers (>60) are treated as minutes."""
        result = parse_time_input("90")
        assert result is not None
        assert result.hours == 1.5
        assert result.confidence >= 0.8


class TestParseTimeInputEdgeCases:
    """Tests for edge cases."""

    def test_empty_string_returns_none(self) -> None:
        """Empty string returns None."""
        assert parse_time_input("") is None

    def test_whitespace_only_returns_none(self) -> None:
        """Whitespace only returns None."""
        assert parse_time_input("   ") is None

    def test_invalid_input_returns_none(self) -> None:
        """Invalid input returns None."""
        assert parse_time_input("hello") is None
        assert parse_time_input("abc123") is None

    def test_case_insensitive(self) -> None:
        """Parsing is case insensitive."""
        assert parse_time_input("2 HOURS") is not None
        assert parse_time_input("30 Min") is not None
        assert parse_time_input("1H") is not None

    def test_handles_leading_trailing_whitespace(self) -> None:
        """Handles leading/trailing whitespace."""
        result = parse_time_input("  2 hours  ")
        assert result is not None
        assert result.hours == 2.0

    def test_zero_returns_none(self) -> None:
        """Zero input returns None."""
        assert parse_time_input("0") is None
        assert parse_time_input("0h") is not None  # Explicit 0h is valid


class TestFormatHours:
    """Tests for format_hours function."""

    def test_formats_hours_only(self) -> None:
        """Formats whole hours as 'Xh'."""
        assert format_hours(1.0) == "1h"
        assert format_hours(2.0) == "2h"
        assert format_hours(10.0) == "10h"

    def test_formats_minutes_only(self) -> None:
        """Formats sub-hour as 'Xm'."""
        assert format_hours(0.25) == "15m"
        assert format_hours(0.5) == "30m"
        assert format_hours(0.75) == "45m"

    def test_formats_hours_and_minutes(self) -> None:
        """Formats hours and minutes as 'Xh Ym'."""
        assert format_hours(1.5) == "1h 30m"
        assert format_hours(2.25) == "2h 15m"
        assert format_hours(3.75) == "3h 45m"

    def test_formats_zero(self) -> None:
        """Formats zero as '0m'."""
        assert format_hours(0.0) == "0m"

    def test_formats_negative_as_zero(self) -> None:
        """Formats negative as '0m'."""
        assert format_hours(-1.0) == "0m"
