"""PydanticAI agent configuration for commitment management assistance."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.models import Model
from sqlmodel import Session

from jdo.config import get_settings

# System prompt for the commitment tracking agent
SYSTEM_PROMPT = """You are a commitment tracking assistant for the JDO application.
You help users manage their commitments by:
- Tracking what they've promised to deliver
- Reminding them of upcoming deadlines
- Helping them break down work into tasks
- Suggesting priorities based on due dates and stakeholder importance

Be concise and action-oriented. Focus on helping users keep their commitments."""


@dataclass
class JDODependencies:
    """Runtime dependencies for the AI agent.

    Provides access to database session and user context.
    """

    session: Session
    timezone: str = "America/New_York"


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
        system_prompt=SYSTEM_PROMPT,
    )
    if with_tools:
        # Late import to avoid circular dependency
        from jdo.ai.tools import register_tools

        register_tools(agent)
    return agent


def create_agent() -> Agent[JDODependencies, str]:
    """Create a PydanticAI agent configured for commitment tracking.

    Uses the model specified in settings.

    Returns:
        A configured Agent instance.
    """
    return create_agent_with_model(get_model_identifier())
