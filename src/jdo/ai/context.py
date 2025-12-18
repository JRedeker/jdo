"""AI context management for conversational TUI.

Handles message formatting, system prompts, and streaming support
for the JDO conversational interface.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse

from jdo.ai.agent import JDODependencies

# Maximum number of messages to include in context (excluding system prompt)
MAX_CONTEXT_MESSAGES = 50

# System prompt for the JDO conversational AI
JDO_SYSTEM_PROMPT = """\
You are JDO, a commitment tracking assistant that helps users manage their promises.

## Your Role
You help users:
- Capture commitments (what they promised to deliver, to whom, and by when)
- Track goals and their associated milestones
- Break down commitments into actionable tasks
- Review their progress and prioritize work

## Key Concepts
- **Commitment**: A promise to deliver something to a stakeholder by a specific date/time
- **Goal**: A larger objective that multiple commitments may serve
- **Milestone**: A checkpoint within a goal with a target date
- **Task**: A specific action item within a commitment
- **Stakeholder**: A person or group to whom commitments are made

## Slash Commands
Users can use these commands to create and manage data:
- `/commit` - Create a new commitment from the conversation
- `/goal` - Create a new goal
- `/task` - Add a task to the current commitment
- `/vision` - Create or review visions
- `/milestone` - Create a milestone for a goal
- `/show <type>` - Display goals, commitments, or tasks
- `/view <id>` - View a specific item
- `/complete` - Mark an item as completed
- `/help` - Show available commands

## Extraction Guidelines
When users describe commitments, extract:
- **Deliverable**: What specifically will be delivered (be precise)
- **Stakeholder**: Who is this for (person, team, or organization)
- **Due date**: When it's due (be specific: date and time if mentioned)

When users describe goals, extract:
- **Title**: A concise name for the goal
- **Problem statement**: What problem this goal solves
- **Solution vision**: What success looks like

## Conversation Style
- Be concise and action-oriented
- Focus on capturing commitments accurately
- Ask clarifying questions when details are missing
- Confirm extracted data before creating records
- Help users think through their commitments clearly
"""


def get_system_prompt() -> str:
    """Get the system prompt for JDO conversations.

    Returns:
        The system prompt string with JDO-specific instructions.
    """
    return JDO_SYSTEM_PROMPT


def format_message(message: dict[str, str]) -> dict[str, str]:
    """Format a single message for the AI API.

    Args:
        message: Dict with 'role' and 'content' keys.

    Returns:
        Formatted message dict with role and content.
    """
    return {
        "role": message["role"],
        "content": message["content"],
    }


def format_conversation(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Format a conversation history for the AI API.

    Args:
        messages: List of message dicts with 'role' and 'content'.

    Returns:
        List of formatted message dicts.
    """
    return [format_message(msg) for msg in messages]


def build_context(
    messages: list[dict[str, str]],
    *,
    include_system: bool = True,
) -> list[dict[str, str]]:
    """Build conversation context for AI, with optional truncation.

    Args:
        messages: List of conversation messages.
        include_system: Whether to prepend the system prompt.

    Returns:
        List of formatted messages, truncated if needed.
    """
    # Format messages
    formatted = format_conversation(messages)

    # Truncate if needed (keep most recent)
    if len(formatted) > MAX_CONTEXT_MESSAGES:
        formatted = formatted[-MAX_CONTEXT_MESSAGES:]

    # Prepend system prompt if requested
    if include_system:
        system_msg = {"role": "system", "content": get_system_prompt()}
        return [system_msg, *formatted]

    return formatted


def _convert_to_model_messages(
    messages: list[dict[str, str]],
) -> list[ModelRequest | ModelResponse]:
    """Convert simple message dicts to PydanticAI ModelMessage objects.

    Args:
        messages: List of dicts with 'role' and 'content' keys.

    Returns:
        List of ModelRequest (user) or ModelResponse (assistant) objects.
    """
    from pydantic_ai.messages import TextPart, UserPromptPart

    result: list[ModelRequest | ModelResponse] = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            result.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        elif role == "assistant":
            result.append(ModelResponse(parts=[TextPart(content=content)]))
        # Skip system messages - they're handled via system_prompt in agent

    return result


async def stream_response(
    agent: Agent[JDODependencies, str],
    prompt: str,
    deps: JDODependencies,
    message_history: list[dict[str, str]] | None = None,
) -> AsyncIterator[str]:
    """Stream AI response chunks.

    Args:
        agent: The PydanticAI agent to use.
        prompt: The user's prompt.
        deps: Agent dependencies including database session.
        message_history: Optional conversation history for multi-turn context.

    Yields:
        Text chunks as they arrive from the AI.
    """
    # Convert message history to PydanticAI format if provided
    model_history = None
    if message_history:
        model_history = _convert_to_model_messages(message_history)

    async with agent.run_stream(prompt, deps=deps, message_history=model_history) as result:
        async for chunk in result.stream_text():
            yield chunk
