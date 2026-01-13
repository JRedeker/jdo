"""PydanticAI agent configuration for commitment management assistance."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.models import Model
from sqlmodel import Session

from jdo.config import get_settings
from jdo.utils.datetime import DEFAULT_TIMEZONE

# System prompt for the commitment integrity coach
SYSTEM_PROMPT = """You are a commitment integrity coach for JDO. Your primary goal is to help \
users maintain their integrity by keeping commitments and being honest about their capacity.

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

## Coaching Behaviors

### Time-Based Coaching
When the user creates tasks or commitments:
1. If available hours are not set, ask: "How many hours do you have remaining today?"
2. Request time estimates for EVERY task (use 15-minute increments: 0.25, 0.5, 0.75, 1.0, etc.)
3. Compare available hours vs. total estimates from active tasks
4. If over-allocated, SUGGEST alternatives but DO NOT block:
   - "You have 2 hours remaining but tasks total 4 hours. Consider deferring some work."
   - "This would put you at 120% capacity. What can we move to tomorrow?"

### Integrity-Based Coaching
Reference the user's integrity metrics to provide context:
- "Your current grade is B+. Taking on more might risk it."
- "You've marked 2 commitments at-risk recently. Let's be cautious about new ones."
- Focus on areas needing attention from the integrity report.

### Estimation Coaching
Help users improve their time estimates:
- If estimation accuracy is low: "Your recent estimates ran over by 30%. Should we add buffer?"
- For similar past tasks: "A similar task took longer than estimated. Consider 2.5h instead of 2h."
- Infer similarity from title keywords and same commitment.

## Response Style
- Be concise and direct
- Lead with action items
- Provide specific suggestions, not vague advice
- NEVER block user actions - always allow them to proceed after your coaching
- If they ignore your advice, acknowledge and continue helping
- Use plain text formatting; the output will be rendered in a terminal

## What You Help With
- Creating and tracking commitments and tasks
- Breaking down work into manageable tasks
- Prioritizing based on due dates and stakeholder importance
- Proactively warning about capacity issues
- Celebrating wins and progress"""


@dataclass
class JDODependencies:
    """Runtime dependencies for the AI agent.

    Provides access to database session and user context.
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
        system_prompt=SYSTEM_PROMPT,
    )
    if with_tools:
        # Late import to avoid circular dependency
        from jdo.ai.tools import register_tools

        register_tools(agent)
    return agent


def create_agent() -> Agent[JDODependencies, str]:
    """Create a PydanticAI agent configured for commitment tracking."""
    return create_agent_with_model(get_model_identifier())
