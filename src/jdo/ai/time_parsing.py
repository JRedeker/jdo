"""Natural language time parsing for task estimates.

Parses inputs like "2 hours", "30 min", "1.5h", "90 minutes" into
floating-point hours rounded to 15-minute increments (0.25, 0.5, 0.75, 1.0, etc.).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

# 15-minute increment in hours
TIME_INCREMENT = 0.25

# Thresholds for interpreting plain numbers
PLAIN_NUMBER_HOURS_THRESHOLD = 12  # Below this, treat as hours
PLAIN_NUMBER_DEFINITELY_MINUTES = 60  # Above this, definitely minutes


@dataclass
class ParsedTime:
    """Result of parsing a time string.

    Attributes:
        hours: Time in hours, rounded to 15-minute increments.
        original: Original input string.
        confidence: Confidence in the parse (1.0 = certain, < 1.0 = ambiguous).
    """

    hours: float
    original: str
    confidence: float = 1.0


def round_to_increment(hours: float) -> float:
    """Round hours to nearest 15-minute increment, rounding UP for ambiguous values.

    Per design: "Ambiguous inputs rounded up."

    Args:
        hours: Hours as a float.

    Returns:
        Hours rounded to 0.25 increments.
    """
    if hours <= 0:
        return 0.0
    return math.ceil(hours / TIME_INCREMENT) * TIME_INCREMENT


def parse_time_input(text: str) -> ParsedTime | None:
    """Parse a natural language time input into hours.

    Handles formats:
    - "2 hours", "2 hrs", "2h"
    - "30 minutes", "30 mins", "30 min", "30m"
    - "1.5 hours", "1.5h"
    - "1:30" (hours:minutes)
    - "90" (assumed minutes if < 24, else hours if ambiguous)
    - Plain numbers with unit inference

    Args:
        text: Natural language time string.

    Returns:
        ParsedTime with hours rounded to 15-minute increments, or None if unparseable.
    """
    if not text or not text.strip():
        return None

    text = text.strip().lower()

    # Try hours:minutes format (e.g., "1:30")
    result = _parse_colon_format(text)
    if result:
        return result

    # Try hours format (e.g., "2 hours", "2h", "2.5 hrs")
    result = _parse_hours_format(text)
    if result:
        return result

    # Try minutes format (e.g., "30 minutes", "30m", "30 min")
    result = _parse_minutes_format(text)
    if result:
        return result

    # Try plain number (context-dependent)
    result = _parse_plain_number(text)
    if result:
        return result

    return None


def _parse_colon_format(text: str) -> ParsedTime | None:
    """Parse hours:minutes format (e.g., "1:30")."""
    match = re.match(r"^(\d+):(\d{1,2})$", text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        total_hours = hours + minutes / 60.0
        return ParsedTime(
            hours=round_to_increment(total_hours),
            original=text,
            confidence=1.0,
        )
    return None


def _parse_hours_format(text: str) -> ParsedTime | None:
    """Parse hour-based formats (e.g., "2 hours", "2h", "2.5 hrs")."""
    patterns = [
        r"^(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)$",  # "2 hours", "2h", "2.5hrs"
        r"^(\d+(?:\.\d+)?)\s+(?:hours?|hrs?|h)$",  # "2 hours" with space
    ]
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            hours = float(match.group(1))
            return ParsedTime(
                hours=round_to_increment(hours),
                original=text,
                confidence=1.0,
            )
    return None


def _parse_minutes_format(text: str) -> ParsedTime | None:
    """Parse minute-based formats (e.g., "30 minutes", "30m", "30 min")."""
    patterns = [
        r"^(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m)$",  # "30 minutes", "30m"
        r"^(\d+(?:\.\d+)?)\s+(?:minutes?|mins?|m)$",  # "30 min" with space
    ]
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            minutes = float(match.group(1))
            hours = minutes / 60.0
            return ParsedTime(
                hours=round_to_increment(hours),
                original=text,
                confidence=1.0,
            )
    return None


def _parse_plain_number(text: str) -> ParsedTime | None:
    """Parse plain numbers with contextual inference.

    Rules:
    - Numbers < PLAIN_NUMBER_HOURS_THRESHOLD (12): Could be hours (low confidence)
    - Numbers 12-60: Likely minutes
    - Numbers > PLAIN_NUMBER_DEFINITELY_MINUTES (60): Definitely minutes
    """
    match = re.match(r"^(\d+(?:\.\d+)?)$", text)
    if not match:
        return None

    value = float(match.group(1))

    if value <= 0:
        return None

    # Large numbers are definitely minutes
    if value > PLAIN_NUMBER_DEFINITELY_MINUTES:
        hours = value / 60.0
        return ParsedTime(
            hours=round_to_increment(hours),
            original=text,
            confidence=0.8,  # Reasonable confidence it's minutes
        )

    # Medium numbers (12-60) likely minutes
    if value >= PLAIN_NUMBER_HOURS_THRESHOLD:
        hours = value / 60.0
        return ParsedTime(
            hours=round_to_increment(hours),
            original=text,
            confidence=0.7,  # Lower confidence - could be hours for "12"
        )

    # Small numbers (<12) ambiguous - treat as hours
    return ParsedTime(
        hours=round_to_increment(value),
        original=text,
        confidence=0.6,  # Low confidence - could be hours or minutes
    )


def format_hours(hours: float) -> str:
    """Format hours as a human-readable string.

    Args:
        hours: Time in hours.

    Returns:
        Formatted string like "2h", "30m", "1h 30m".
    """
    if hours <= 0:
        return "0m"

    total_minutes = int(hours * 60)
    h = total_minutes // 60
    m = total_minutes % 60

    if h == 0:
        return f"{m}m"
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"
