"""Pattern summary formatter for recurring commitments."""

from jdo.models.recurring_commitment import RecurrenceType, RecurringCommitment

# Day names for display
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Month names for display
MONTH_NAMES = [
    "",  # 0-indexed placeholder
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

# Ordinal suffix constants
ORDINAL_TEEN_MIN = 11
ORDINAL_TEEN_MAX = 13

# Week of month constants for "last" week
# Both 5 and -1 represent "last week of month" for compatibility
LAST_WEEK_VALUES = {5, -1}


def ordinal_suffix(n: int) -> str:
    """Get ordinal suffix for a number (1st, 2nd, 3rd, etc.).

    Args:
        n: The number to get the ordinal for.

    Returns:
        The number with its ordinal suffix (e.g., "1st", "2nd", "3rd").
    """
    # Special cases for 11, 12, 13
    if ORDINAL_TEEN_MIN <= n % 100 <= ORDINAL_TEEN_MAX:
        return f"{n}th"

    # Standard suffixes based on last digit
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    return f"{n}{suffixes.get(n % 10, 'th')}"


def _format_days(days_of_week: list[int]) -> str:
    """Format a list of day indices as day names.

    Args:
        days_of_week: List of day indices (0=Monday to 6=Sunday).

    Returns:
        Formatted string like "Mon, Wed, Fri".
    """
    sorted_days = sorted(days_of_week)
    return ", ".join(DAY_NAMES[d] for d in sorted_days)


def _format_daily(recurring: RecurringCommitment) -> str:
    """Format daily recurrence pattern."""
    if recurring.interval == 1:
        return "Daily"
    return f"Every {recurring.interval} days"


def _format_weekly(recurring: RecurringCommitment) -> str:
    """Format weekly recurrence pattern."""
    days = _format_days(recurring.days_of_week or [])

    if recurring.interval == 1:
        return f"Weekly on {days}"
    return f"Every {recurring.interval} weeks on {days}"


def _format_monthly(recurring: RecurringCommitment) -> str:
    """Format monthly recurrence pattern."""
    # Determine the day pattern
    if recurring.day_of_month is not None:
        day_part = f"the {ordinal_suffix(recurring.day_of_month)}"
    elif recurring.week_of_month is not None and recurring.days_of_week:
        day_name = DAY_NAMES[recurring.days_of_week[0]]
        if recurring.week_of_month in LAST_WEEK_VALUES:
            day_part = f"the last {day_name}"
        else:
            day_part = f"the {ordinal_suffix(recurring.week_of_month)} {day_name}"
    else:
        day_part = ""

    if recurring.interval == 1:
        return f"Monthly on {day_part}"
    return f"Every {recurring.interval} months on {day_part}"


def _format_yearly(recurring: RecurringCommitment) -> str:
    """Format yearly recurrence pattern."""
    month_name = MONTH_NAMES[recurring.month_of_year or 1]

    # Determine the day pattern
    if recurring.day_of_month is not None:
        day_part = f"{month_name} {recurring.day_of_month}"
    elif recurring.week_of_month is not None and recurring.days_of_week:
        day_name = DAY_NAMES[recurring.days_of_week[0]]
        if recurring.week_of_month in LAST_WEEK_VALUES:
            day_part = f"the last {day_name} of {month_name}"
        else:
            day_part = f"the {ordinal_suffix(recurring.week_of_month)} {day_name} of {month_name}"
    else:
        day_part = month_name

    if recurring.interval == 1:
        return f"Yearly on {day_part}"
    return f"Every {recurring.interval} years on {day_part}"


def format_pattern_summary(recurring: RecurringCommitment) -> str:
    """Format a human-readable summary of the recurrence pattern.

    Args:
        recurring: The recurring commitment to format.

    Returns:
        A human-readable string like "Weekly on Mon, Wed, Fri" or
        "Monthly on the 15th".

    Examples:
        >>> format_pattern_summary(daily_recurring)
        "Daily"
        >>> format_pattern_summary(weekly_mon_wed_fri)
        "Weekly on Mon, Wed, Fri"
        >>> format_pattern_summary(monthly_15th)
        "Monthly on the 15th"
        >>> format_pattern_summary(yearly_march_15)
        "Yearly on Mar 15"
    """
    formatters = {
        RecurrenceType.DAILY: _format_daily,
        RecurrenceType.WEEKLY: _format_weekly,
        RecurrenceType.MONTHLY: _format_monthly,
        RecurrenceType.YEARLY: _format_yearly,
    }

    formatter = formatters.get(recurring.recurrence_type)
    if formatter:
        return formatter(recurring)

    return str(recurring.recurrence_type.value).capitalize()
