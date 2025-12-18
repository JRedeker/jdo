"""Natural language date and time parsing for commitments.

Parses expressions like "tomorrow", "next Friday", "December 20", "3pm".
"""

import re
from datetime import UTC, date, datetime, time, timedelta

from jdo.exceptions import ExtractionError

# Days of week (lowercase for matching)
DAYS_OF_WEEK = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

# Short day names
SHORT_DAYS = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

# Month names (lowercase for matching)
MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

# Short month names
SHORT_MONTHS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

# Vague terms that should be rejected
VAGUE_TERMS = {"next week", "soon", "later", "asap", "eventually", "sometime"}

# Named times
NAMED_TIMES = {
    "noon": time(12, 0),
    "midnight": time(0, 0),
    "end of day": time(17, 0),
    "eod": time(17, 0),
}

# Default time when not specified
DEFAULT_TIME = time(9, 0)

# 12-hour clock constants
NOON_HOUR = 12
MIDNIGHT_HOUR = 0


class ParseError(ExtractionError):
    """Raised when date/time cannot be parsed."""


class VagueDateError(ParseError):
    """Raised when date expression is too vague."""


def today_date() -> date:
    """Get today's date (UTC).

    Returns:
        Today's date.
    """
    return datetime.now(UTC).date()


def _parse_relative_date(text: str, today: date) -> date | None:
    """Try to parse relative date expressions.

    Args:
        text: Normalized (lowercase, stripped) text.
        today: Today's date.

    Returns:
        Parsed date or None if not a relative expression.
    """
    if text == "today":
        return today

    if text == "tomorrow":
        return today + timedelta(days=1)

    # Handle "next <day>" or "this <day>"
    for prefix in ("next ", "this "):
        if text.startswith(prefix):
            day_name = text[len(prefix) :]
            target_dow = DAYS_OF_WEEK.get(day_name)
            if target_dow is None:
                target_dow = SHORT_DAYS.get(day_name)
            if target_dow is not None:
                return _next_weekday(today, target_dow, is_this=prefix == "this ")

    return None


def _parse_absolute_date(text: str, today: date) -> date | None:
    """Try to parse absolute date expressions.

    Args:
        text: Normalized (lowercase, stripped) text.
        today: Today's date.

    Returns:
        Parsed date or None if not an absolute date expression.

    Raises:
        ParseError: If the date format is recognized but invalid.
    """
    # Handle ISO format (2025-12-25)
    iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", text)
    if iso_match:
        year, month, day = map(int, iso_match.groups())
        return date(year, month, day)

    # Handle US format (12/25/2025)
    us_match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", text)
    if us_match:
        month, day, year = map(int, us_match.groups())
        return date(year, month, day)

    # Handle "Month Day" format (December 20, Dec 20, December 20th)
    month_day_match = re.match(r"^([a-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?$", text)
    if month_day_match:
        month_name, day_str = month_day_match.groups()
        day_num = int(day_str)

        month_num = MONTHS.get(month_name) or SHORT_MONTHS.get(month_name)
        if month_num:
            try:
                result = date(today.year, month_num, day_num)
                # If date has passed, use next year
                if result < today:
                    result = date(today.year + 1, month_num, day_num)
            except ValueError as e:
                msg = f"Invalid date: {text}"
                raise ParseError(msg) from e
            else:
                return result

    return None


def parse_date(text: str) -> date:
    """Parse a natural language date expression.

    Args:
        text: Date expression like "tomorrow", "next Friday", "December 20".

    Returns:
        Parsed date.

    Raises:
        ParseError: If the date cannot be parsed.
        VagueDateError: If the date expression is too vague.
    """
    if not text or not text.strip():
        msg = "Empty date string"
        raise ParseError(msg)

    text = text.strip().lower()

    # Check for vague terms
    if text in VAGUE_TERMS:
        msg = f"'{text}' is too vague - please specify a concrete date"
        raise VagueDateError(msg)

    today = today_date()

    # Try relative dates first
    result = _parse_relative_date(text, today)
    if result is not None:
        return result

    # Try absolute dates
    result = _parse_absolute_date(text, today)
    if result is not None:
        return result

    msg = f"Could not parse date: '{text}'"
    raise ParseError(msg)


def _next_weekday(from_date: date, target_dow: int, *, is_this: bool) -> date:
    """Get the next occurrence of a weekday.

    Args:
        from_date: Starting date.
        target_dow: Target day of week (0=Monday, 6=Sunday).
        is_this: If True, allow returning from_date if it's already target_dow.

    Returns:
        Next occurrence of the target weekday.
    """
    current_dow = from_date.weekday()

    if is_this and current_dow == target_dow:
        return from_date

    days_ahead = target_dow - current_dow
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7

    return from_date + timedelta(days=days_ahead)


def parse_time(text: str) -> time:
    """Parse a natural language time expression.

    Args:
        text: Time expression like "3pm", "15:00", "end of day".

    Returns:
        Parsed time.

    Raises:
        ParseError: If the time cannot be parsed.
    """
    if not text or not text.strip():
        msg = "Empty time string"
        raise ParseError(msg)

    text = text.strip().lower()

    # Check for named times first
    if text in NAMED_TIMES:
        return NAMED_TIMES[text]

    # Try parsing as 12-hour format
    result = _parse_12h_time(text)
    if result is not None:
        return result

    # Try parsing as 24-hour format
    result = _parse_24h_time(text)
    if result is not None:
        return result

    msg = f"Could not parse time: '{text}'"
    raise ParseError(msg)


def _parse_12h_time(text: str) -> time | None:
    """Parse 12-hour format time (3pm, 3:30pm, etc.)."""
    match = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", text)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    period = match.group(3)

    if period == "pm" and hour != NOON_HOUR:
        hour += NOON_HOUR
    elif period == "am" and hour == NOON_HOUR:
        hour = MIDNIGHT_HOUR

    return time(hour, minute)


def _parse_24h_time(text: str) -> time | None:
    """Parse 24-hour format time (15:00, etc.)."""
    match = re.match(r"^(\d{1,2}):(\d{2})$", text)
    if not match:
        return None
    hour, minute = map(int, match.groups())
    return time(hour, minute)


def parse_datetime(text: str) -> tuple[date, time]:
    """Parse a combined date and optional time expression.

    Args:
        text: Date/time expression like "tomorrow at 3pm", "December 20 by 5pm".

    Returns:
        Tuple of (parsed_date, parsed_time). Time defaults to 09:00 if not specified.

    Raises:
        ParseError: If the date cannot be parsed.
        VagueDateError: If the date expression is too vague.
    """
    if not text or not text.strip():
        msg = "Empty datetime string"
        raise ParseError(msg)

    text = text.strip()

    # Try to split on "at" or "by"
    for separator in (" at ", " by "):
        if separator in text.lower():
            parts = text.lower().split(separator, 1)
            date_part = parts[0].strip()
            time_part = parts[1].strip()

            parsed_date = parse_date(date_part)
            parsed_time = parse_time(time_part)
            return (parsed_date, parsed_time)

    # No time separator found - parse as date only
    parsed_date = parse_date(text)
    return (parsed_date, DEFAULT_TIME)
