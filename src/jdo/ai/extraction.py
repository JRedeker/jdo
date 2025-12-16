"""AI field extraction for commitments, goals, and tasks.

Uses PydanticAI structured output to extract fields from natural language.
"""

from datetime import date, time
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models import Model

from jdo.ai.context import get_system_prompt

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


def create_extraction_agent(
    model: Model | str,
    output_type: type[BaseModel],
    extraction_prompt: str,
) -> Agent[None, BaseModel]:
    """Create an agent for extracting structured data.

    Args:
        model: The model to use for extraction.
        output_type: The Pydantic model type to extract.
        extraction_prompt: Additional prompt for extraction guidance.

    Returns:
        A configured Agent for extraction.
    """
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
    """
    agent = create_extraction_agent(model, ExtractedCommitment, COMMITMENT_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await agent.run(conversation)
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
    """
    agent = create_extraction_agent(model, ExtractedGoal, GOAL_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await agent.run(conversation)
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
    """
    agent = create_extraction_agent(model, ExtractedTask, TASK_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await agent.run(conversation)
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
    """
    agent = create_extraction_agent(model, ExtractedVision, VISION_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await agent.run(conversation)
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
    """
    agent = create_extraction_agent(model, ExtractedMilestone, MILESTONE_EXTRACTION_PROMPT)
    conversation = _format_conversation_for_extraction(messages)

    result = await agent.run(conversation)
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
