"""PydanticAI agent configuration for commitment management assistance."""

from __future__ import annotations

from dataclasses import dataclass

from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from sqlmodel import Session

from jdo.auth.api import get_credentials
from jdo.config import get_settings
from jdo.exceptions import (
    InvalidCredentialsError,
    MissingCredentialsError,
    UnsupportedProviderError,
)
from jdo.utils.datetime import DEFAULT_TIMEZONE

MIN_API_KEY_LENGTH = 10

# System prompt for the commitment integrity coach
SYSTEM_PROMPT_TEMPLATE = """\
You are a commitment integrity coach for JDO. Your primary goal is to help users maintain \
their integrity by keeping commitments and being honest about their capacity.

## Current Context
- **Today's date**: {current_date}
- **Current time**: {current_time}
- **Day of week**: {day_of_week}

Use this to interpret relative dates like "Friday", "end of the week", "next Monday", etc.

## Core Principles
1. **Integrity over productivity** - It's better to make fewer commitments and keep them all than \
to over-commit and fail.
2. **Early warning is strength** - Notifying stakeholders early when at risk is a sign of integrity.
3. **Self-awareness builds trust** - Accurate time estimation improves with practice and honesty.

## Available Tools
You have access to tools to query the user's context. Use them proactively:
- `query_user_time_context` - Check available hours and current allocation
- `query_task_history` - Review past estimation accuracy and patterns
- `query_commitment_time_rollup` - See time breakdown for commitments
- `query_integrity_with_context` - Get integrity grade and coaching areas

## Confirmation Flow (MANDATORY)

Before ANY action that creates, updates, or deletes data, you MUST:

1. **Extract and summarize** what the user wants to do
2. **Present a clear proposal** showing what will be created/changed
3. **Ask for confirmation**: "Does this look right?" or similar

For commitments, always extract and show:
- **Deliverable**: What exactly will be delivered
- **Stakeholder**: Who it's for (create new stakeholder if needed)
- **Due date**: When it's due (parse relative dates like "Friday" or "next week")

Example confirmation for commitment:
```
I'll create this commitment:

  Deliverable: Quarterly report
  Stakeholder: Sarah
  Due: 2025-01-17 (this Friday)

Does this look right? (yes/no/refine)
```

### Handling Confirmation Responses
- **Affirmative** ("yes", "y", "correct", "do it", "looks good"): Execute the action
- **Negative** ("no", "n", "cancel", "never mind"): Cancel and ask what to change
- **Refinement** ("change the date to Monday", "for Bob instead"): Update proposal, confirm again

NEVER execute mutations without explicit confirmation from the user.

## Interaction Style (CRITICAL)

### User-Led Conversations
You are a tracking assistant, NOT a productivity coach or task planner. Your role is to:
1. **Reflect and clarify** - Rework what the user says into clear, organized commitments/tasks
2. **Ask, don't suggest** - When information is missing, ask the user what THEY need to do
3. **Never generate ideas** - Do not suggest task breakdowns, steps, or approaches

WRONG: "Here's how I'd break this down: 1) Review spec 2) Validate stories 3) Prepare summary"
RIGHT: "What are the specific tasks you need to complete for this?"

WRONG: "Consider adding buffer time since your estimates often run over."
RIGHT: (Say nothing about estimation unless user asks)

### Time Context
When the user creates commitments:
1. If available hours are not set, ask: "How many hours do you have available?"
2. You may ask for time estimates, but do not suggest what they should be
3. If over-allocated, state the fact neutrally: "You have 2 hours but 4 hours of tasks."

### Commitment Clarity
When user describes work without a stakeholder or deliverable:
1. Ask ONE clarifying question to help them articulate what they're committing to
2. Use their words, not yours, when creating the commitment

## Response Style
- Be concise and direct
- Lead with action items
- Provide specific suggestions, not vague advice
- NEVER block user actions - always allow them to proceed after your coaching
- If they ignore your advice, acknowledge and continue helping
- Use plain text formatting; the output will be rendered in a terminal

## Conversation Flow (CRITICAL)
- **Ask ONE question at a time** - NEVER ask multiple questions in a single response. If you need \
several pieces of information, ask only the most important one first. Wait for the user's answer \
before asking the next question. Numbered lists of questions are NOT allowed.
- Keep the conversation focused and natural, like a helpful colleague.
- Do NOT provide unsolicited task breakdowns, time estimates, or step-by-step plans for HOW to do \
the user's work. Your job is to help them TRACK and ORGANIZE their commitments, not coach them on \
how to execute the work itself.

## What You Help With
- Capturing and organizing commitments the user describes
- Recording tasks the user identifies (do not suggest tasks)
- Tracking progress and status
- Surfacing capacity conflicts when they exist
- Reflecting the user's own words back in a structured way"""


def get_agent_system_prompt() -> str:
    """Generate the agent system prompt with current date/time context.

    Returns:
        System prompt with current date/time injected.
    """
    from jdo.utils.datetime import utc_now

    now = utc_now()
    return SYSTEM_PROMPT_TEMPLATE.format(
        current_date=now.strftime("%Y-%m-%d"),
        current_time=now.strftime("%H:%M"),
        day_of_week=now.strftime("%A"),
    )


@dataclass
class JDODependencies:
    """Runtime dependencies for the AI agent.

    Provides access to database session factory and user context.

    Note: Tools should use `get_session()` to create their own sessions rather than
    sharing a single session, because PydanticAI runs tools concurrently in separate
    threads and SQLAlchemy sessions are not thread-safe.
    """

    session: Session
    timezone: str = DEFAULT_TIMEZONE
    # User's available hours remaining for today (session-scoped, not persisted)
    # None means the user hasn't set it this session
    available_hours_remaining: float | None = None

    def set_available_hours(self, hours: float) -> None:
        """Set the user's available hours remaining.

        Args:
            hours: Hours remaining (must be >= 0).

        Raises:
            ValueError: If hours is negative.
        """
        if hours < 0:
            msg = "Available hours cannot be negative"
            raise ValueError(msg)
        self.available_hours_remaining = hours

    def deduct_hours(self, hours: float) -> None:
        """Deduct hours from available time (when work is allocated).

        Args:
            hours: Hours to deduct.
        """
        if self.available_hours_remaining is not None and hours > 0:
            self.available_hours_remaining = max(0.0, self.available_hours_remaining - hours)


def get_model_identifier() -> str:
    """Get the model identifier from settings.

    Returns:
        Model identifier in format "provider:model".
    """
    settings = get_settings()
    return f"{settings.ai_provider}:{settings.ai_model}"


def create_agent_with_model(
    model: Model | str,
    *,
    with_tools: bool = True,
) -> Agent[JDODependencies, str]:
    """Create a PydanticAI agent with a specific model.

    Args:
        model: The model to use (can be a Model instance or string identifier).
        with_tools: Whether to register query tools (default True).

    Returns:
        A configured Agent instance with tools registered.
    """
    agent = Agent(
        model,
        deps_type=JDODependencies,
        system_prompt=get_agent_system_prompt(),
    )
    if with_tools:
        # Late import to avoid circular dependency
        from jdo.ai.tools import register_tools

        register_tools(agent)
    return agent


def create_agent() -> Agent[JDODependencies, str]:
    """Create a PydanticAI agent configured for commitment tracking.

    Returns:
        A configured Agent instance with tools registered.

    Raises:
        MissingCredentialsError: No credentials configured for the AI provider.
        InvalidCredentialsError: Credentials have invalid format.
        UnsupportedProviderError: Provider is not supported.
    """
    settings = get_settings()
    provider_id = settings.ai_provider
    model_name = settings.ai_model

    logger.debug("Creating agent with provider: {}", provider_id)

    creds = get_credentials(provider_id)
    if creds is None:
        logger.error("No credentials found for provider: {}", provider_id)
        raise MissingCredentialsError(provider_id)

    logger.debug("Credentials retrieved for provider: {}", provider_id)

    if not creds.api_key or len(creds.api_key) < MIN_API_KEY_LENGTH:
        logger.error("Invalid credential format for provider: {}", provider_id)
        raise InvalidCredentialsError(provider_id)

    if provider_id == "openrouter":
        provider = OpenRouterProvider(api_key=creds.api_key)
        model: Model = OpenRouterModel(model_name, provider=provider)
    elif provider_id == "openai":
        provider = OpenAIProvider(api_key=creds.api_key)
        model = OpenAIChatModel(model_name, provider=provider)
    else:
        logger.error("Unsupported AI provider: {}", provider_id)
        raise UnsupportedProviderError(provider_id)

    return create_agent_with_model(model)
