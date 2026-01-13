"""AI field extraction for commitments, goals, and tasks.

Uses PydanticAI structured output to extract fields from natural language.
"""

from __future__ import annotations

from datetime import date, time
from typing import Any

from pydantic import BaseModel, Field, model_validator
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider

from jdo.ai.context import get_system_prompt
from jdo.ai.timeout import AI_TIMEOUT_SECONDS, with_ai_timeout
from jdo.auth.api import get_credentials
from jdo.config import get_settings

# Extraction prompts
COMMITMENT_EXTRACTION_PROMPT = """\
Extract commitment details from the conversation. Look for:
- What the user promised to deliver (deliverable)
- Who they're delivering it to (stakeholder_name)
- When it's due (due_date, and due_time if mentioned)

Be specific and precise. Use the exact words the user used when possible.
"""

GOAL_EXTRACTION_PROMPT = """\
Extract goal details from the conversation. Look for:
- A concise title for the goal
- The problem being solved (problem_statement)
- What success looks like (solution_vision)

Be specific and capture the user's intent accurately.
"""

TASK_EXTRACTION_PROMPT = """\
Extract task details from the conversation. Look for:
- A clear title for the task
- The scope of work (what specifically needs to be done)

Be specific and actionable.
"""

VISION_EXTRACTION_PROMPT = """\
Extract vision details from the conversation. A vision is a vivid, inspiring
picture of the future (3-5+ years). Look for:
- A concise title for the vision
- A vivid narrative describing what success looks like (paint a picture!)
- The timeframe (e.g., "3 years", "5 years", "by 2030")
- Metrics that would indicate success (optional)
- Why this matters (optional)

Make the narrative vivid and inspiring - describe what the future looks and feels like.
"""

MILESTONE_EXTRACTION_PROMPT = """\
Extract milestone details from the conversation. A milestone is a concrete
checkpoint with a specific target_date. Look for:
- A clear title for the milestone
- A description of what this milestone represents
- The target_date when this should be achieved

Be specific about the target_date - milestones need concrete dates.
"""

SUGGEST_METRICS_PROMPT = """\
Based on this vision, suggest 3-5 concrete, measurable metrics that would
indicate progress toward or achievement of this vision. Metrics should be:
- Specific and measurable
- Relevant to the vision's goals
- Time-bound where appropriate

Return metrics as a list of strings.
"""

SUGGEST_MILESTONES_PROMPT = """\
Based on this goal, suggest 2-4 concrete milestones that would break down
progress toward the goal. Each milestone should have:
- A clear title
- A description
- A suggested target_date

Milestones should be spaced appropriately to show meaningful progress.
"""

VISION_LINKAGE_PROMPT = """\
The user is creating a new goal. Available visions are listed below.
Suggest which vision this goal might support, or ask if they'd like to
create a new vision for this goal.
"""

MILESTONE_LINKAGE_PROMPT = """\
The user is creating a new commitment. This goal has milestones.
Suggest which milestone this commitment might contribute to, based on
the commitment's deliverable and due date.
"""

RECURRING_COMMITMENT_EXTRACTION_PROMPT = """\
Extract recurring commitment details from the conversation. Look for:
- What the user commits to doing regularly (deliverable_template)
- Who they're committing to (stakeholder_name)
- The recurrence pattern (recurrence_type: daily, weekly, monthly, or yearly)
- For weekly: which days of the week (days_of_week as 0=Monday to 6=Sunday)
- For monthly: either the day of month (1-31) or "Nth weekday" pattern
- Time of day if mentioned (due_time)

Common patterns to recognize:
- "every day", "daily" → daily
- "every Monday", "weekly on Monday" → weekly, days_of_week=[0]
- "every Mon, Wed, Fri" → weekly, days_of_week=[0, 2, 4]
- "every other week" → weekly with interval=2
- "on the 15th of each month" → monthly, day_of_month=15
- "first Monday of each month" → monthly, week_of_month=1, days_of_week=[0]
- "last Friday of each month" → monthly, week_of_month=5, days_of_week=[4]
- "annually on March 15" → yearly, month_of_year=3, day_of_month=15

Be specific about the recurrence pattern.
"""


class ExtractedCommitment(BaseModel):
    """Extracted commitment fields from conversation."""

    deliverable: str = Field(description="What will be delivered")
    stakeholder_name: str = Field(description="Who this is for (person, team, or organization)")
    due_date: date = Field(description="When it's due (YYYY-MM-DD)")
    due_time: time | None = Field(default=None, description="Time of day if specified (HH:MM)")


class ExtractedGoal(BaseModel):
    """Extracted goal fields from conversation."""

    title: str = Field(description="A concise name for the goal")
    problem_statement: str = Field(description="What problem this goal solves")
    solution_vision: str = Field(description="What success looks like")


class ExtractedTask(BaseModel):
    """Extracted task fields from conversation."""

    title: str = Field(description="A clear title for the task")
    scope: str = Field(description="What specifically needs to be done")


class ExtractedVision(BaseModel):
    """Extracted vision fields from conversation."""

    title: str = Field(description="A concise name for the vision")
    narrative: str = Field(description="A vivid description of what success looks like")
    timeframe: str | None = Field(default=None, description="When this should be achieved")
    metrics: list[str] = Field(default_factory=list, description="Measurable indicators of success")
    why_it_matters: str | None = Field(default=None, description="Why this vision matters")


class ExtractedMilestone(BaseModel):
    """Extracted milestone fields from conversation."""

    title: str = Field(description="A clear title for the milestone")
    description: str | None = Field(default=None, description="What this milestone represents")
    target_date: date = Field(description="When this should be achieved (YYYY-MM-DD)")


# Validation constants for extracted recurrence values
MIN_DAY_OF_WEEK = 0
MAX_DAY_OF_WEEK = 6
MIN_DAY_OF_MONTH = 1
MAX_DAY_OF_MONTH = 31
MIN_MONTH_OF_YEAR = 1
MAX_MONTH_OF_YEAR = 12
VALID_WEEK_OF_MONTH = {1, 2, 3, 4, 5, -1}


class ExtractedRecurringCommitment(BaseModel):
    """Extracted recurring commitment fields from conversation."""

    deliverable_template: str = Field(description="What will be delivered each time")
    stakeholder_name: str = Field(description="Who this is for (person, team, or organization)")
    recurrence_type: str = Field(
        description="Type of recurrence: 'daily', 'weekly', 'monthly', or 'yearly'"
    )
    interval: int = Field(
        default=1,
        description="Interval between occurrences (e.g., 2 for 'every other week')",
    )
    days_of_week: list[int] | None = Field(
        default=None,
        description="For weekly: days of week as integers (0=Monday to 6=Sunday)",
    )
    day_of_month: int | None = Field(
        default=None,
        description="For monthly: specific day of month (1-31)",
    )
    week_of_month: int | None = Field(
        default=None,
        description="For monthly: which week (1-4, or 5 for 'last')",
    )
    month_of_year: int | None = Field(
        default=None,
        description="For yearly: month (1-12)",
    )
    due_time: time | None = Field(
        default=None,
        description="Time of day if specified (HH:MM)",
    )

    @model_validator(mode="after")
    def validate_extracted_values(self) -> ExtractedRecurringCommitment:
        """Validate extracted recurrence values are in valid ranges."""
        self._validate_recurrence_type()
        self._validate_days_of_week()
        self._validate_day_of_month()
        self._validate_week_of_month()
        self._validate_month_of_year()
        self._validate_interval()
        return self

    def _validate_recurrence_type(self) -> None:
        """Validate and normalize recurrence_type."""
        valid_types = {"daily", "weekly", "monthly", "yearly"}
        if self.recurrence_type.lower() not in valid_types:
            msg = f"recurrence_type must be one of: {', '.join(valid_types)}"
            raise ValueError(msg)
        self.recurrence_type = self.recurrence_type.lower()

    def _validate_days_of_week(self) -> None:
        """Validate days_of_week values are in range 0-6."""
        if self.days_of_week is None:
            return
        for day in self.days_of_week:
            if not (MIN_DAY_OF_WEEK <= day <= MAX_DAY_OF_WEEK):
                msg = "days_of_week values must be 0-6 (Monday=0 to Sunday=6)"
                raise ValueError(msg)

    def _validate_day_of_month(self) -> None:
        """Validate day_of_month is in range 1-31."""
        if self.day_of_month is None:
            return
        if not (MIN_DAY_OF_MONTH <= self.day_of_month <= MAX_DAY_OF_MONTH):
            msg = "day_of_month must be 1-31"
            raise ValueError(msg)

    def _validate_week_of_month(self) -> None:
        """Validate week_of_month is 1-5 or -1."""
        if self.week_of_month is None:
            return
        if self.week_of_month not in VALID_WEEK_OF_MONTH:
            msg = "week_of_month must be 1-5 or -1 (for last week)"
            raise ValueError(msg)

    def _validate_month_of_year(self) -> None:
        """Validate month_of_year is in range 1-12."""
        if self.month_of_year is None:
            return
        if not (MIN_MONTH_OF_YEAR <= self.month_of_year <= MAX_MONTH_OF_YEAR):
            msg = "month_of_year must be 1-12"
            raise ValueError(msg)

    def _validate_interval(self) -> None:
        """Validate interval is positive."""
        if self.interval < 1:
            msg = "interval must be at least 1"
            raise ValueError(msg)


def _create_model_with_credentials() -> Model:
    """Create a PydanticAI model with credentials from settings.

    Returns:
        A configured Model instance.

    Raises:
        ValueError: If provider is not supported or credentials are missing.
    """
    settings = get_settings()
    provider_id = settings.ai_provider
    model_name = settings.ai_model

    creds = get_credentials(provider_id)
    if creds is None or not creds.api_key:
        msg = f"No credentials found for provider: {provider_id}"
        raise ValueError(msg)

    if provider_id == "openrouter":
        provider = OpenRouterProvider(api_key=creds.api_key)
        return OpenRouterModel(model_name, provider=provider)
    if provider_id == "openai":
        provider = OpenAIProvider(api_key=creds.api_key)
        return OpenAIChatModel(model_name, provider=provider)
    msg = f"Unsupported AI provider: {provider_id}"
    raise ValueError(msg)


def create_extraction_agent(
    model: Model | str,
    output_type: type[BaseModel],
    extraction_prompt: str,
) -> Agent[None, BaseModel]:
    """Create an agent for extracting structured data.

    Args:
        model: The model to use for extraction. If a string is passed,
               credentials will be loaded from settings automatically.
        output_type: The Pydantic model type to extract.
        extraction_prompt: Additional prompt for extraction guidance.

    Returns:
        A configured Agent for extraction.
    """
    # If model is a string identifier (not "test"), create a proper model with credentials
    if isinstance(model, str) and model != "test":
        model = _create_model_with_credentials()

    system_prompt = f"{get_system_prompt()}\n\n{extraction_prompt}"

    return Agent(
        model,
        output_type=output_type,
        system_prompt=system_prompt,
    )


def _format_conversation_for_extraction(messages: list[dict[str, str]]) -> str:
    """Format conversation messages into a single string for extraction.

    Args:
        messages: List of message dicts with 'role' and 'content'.

    Returns:
        Formatted conversation string.
    """
    parts = []
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]
        parts.append(f"{role}: {content}")
    return "\n\n".join(parts)


async def extract_commitment(
    messages: list[dict[str, str]],
    model: Model | str = "test",
) -> ExtractedCommitment:
    """Extract commitment fields from conversation.

    Args:
        messages: Conversation history.
        model: Model to use for extraction.

    Returns:
        ExtractedCommitment with populated fields.

    Raises:
        TimeoutError: If AI call exceeds timeout.
    """
    agent = create_extraction_agent(model, ExtractedCommitment, COMMITMENT_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await with_ai_timeout(agent.run(conversation), AI_TIMEOUT_SECONDS)
    return result.output  # type: ignore[return-value]


async def extract_goal(
    messages: list[dict[str, str]],
    model: Model | str = "test",
) -> ExtractedGoal:
    """Extract goal fields from conversation.

    Args:
        messages: Conversation history.
        model: Model to use for extraction.

    Returns:
        ExtractedGoal with populated fields.

    Raises:
        TimeoutError: If AI call exceeds timeout.
    """
    agent = create_extraction_agent(model, ExtractedGoal, GOAL_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await with_ai_timeout(agent.run(conversation), AI_TIMEOUT_SECONDS)
    return result.output  # type: ignore[return-value]


async def extract_task(
    messages: list[dict[str, str]],
    model: Model | str = "test",
) -> ExtractedTask:
    """Extract task fields from conversation.

    Args:
        messages: Conversation history.
        model: Model to use for extraction.

    Returns:
        ExtractedTask with populated fields.

    Raises:
        TimeoutError: If AI call exceeds timeout.
    """
    agent = create_extraction_agent(model, ExtractedTask, TASK_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await with_ai_timeout(agent.run(conversation), AI_TIMEOUT_SECONDS)
    return result.output  # type: ignore[return-value]


async def extract_vision(
    messages: list[dict[str, str]],
    model: Model | str = "test",
) -> ExtractedVision:
    """Extract vision fields from conversation.

    Args:
        messages: Conversation history.
        model: Model to use for extraction.

    Returns:
        ExtractedVision with populated fields.

    Raises:
        TimeoutError: If AI call exceeds timeout.
    """
    agent = create_extraction_agent(model, ExtractedVision, VISION_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await with_ai_timeout(agent.run(conversation), AI_TIMEOUT_SECONDS)
    return result.output  # type: ignore[return-value]


async def extract_milestone(
    messages: list[dict[str, str]],
    model: Model | str = "test",
) -> ExtractedMilestone:
    """Extract milestone fields from conversation.

    Args:
        messages: Conversation history.
        model: Model to use for extraction.

    Returns:
        ExtractedMilestone with populated fields.

    Raises:
        TimeoutError: If AI call exceeds timeout.
    """
    agent = create_extraction_agent(model, ExtractedMilestone, MILESTONE_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await with_ai_timeout(agent.run(conversation), AI_TIMEOUT_SECONDS)
    return result.output  # type: ignore[return-value]


async def extract_recurring_commitment(
    messages: list[dict[str, str]],
    model: Model | str = "test",
) -> ExtractedRecurringCommitment:
    """Extract recurring commitment fields from conversation.

    Args:
        messages: Conversation history.
        model: Model to use for extraction.

    Returns:
        ExtractedRecurringCommitment with populated fields.

    Raises:
        TimeoutError: If AI call exceeds timeout.
    """
    agent = create_extraction_agent(
        model, ExtractedRecurringCommitment, RECURRING_COMMITMENT_EXTRACTION_PROMPT
    )
    conversation = _format_conversation_for_extraction(messages)

    result = await with_ai_timeout(agent.run(conversation), AI_TIMEOUT_SECONDS)
    return result.output  # type: ignore[return-value]


def get_missing_fields(
    data: dict[str, Any],
    model_type: type[BaseModel],
) -> list[str]:
    """Get list of missing required fields for a model.

    Args:
        data: Partial data dict.
        model_type: The Pydantic model type to check against.

    Returns:
        List of missing required field names.
    """
    required_fields = []

    for name, field_info in model_type.model_fields.items():
        # Field is required if it has no default and is not Optional
        if field_info.is_required():
            required_fields.append(name)

    return [field for field in required_fields if field not in data or data[field] is None]
