"""AI-powered triage classification for captured items.

Uses PydanticAI to classify raw text into appropriate entity types
(commitment, goal, task, vision, milestone) with confidence scoring.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from jdo.ai.timeout import AI_TIMEOUT_SECONDS, run_sync_with_timeout, with_ai_timeout
from jdo.config import get_settings
from jdo.models.draft import EntityType

# Confidence threshold for accepting AI classification
CONFIDENCE_THRESHOLD = 0.7

# Allowed entity types for triage (excludes UNKNOWN)
CLASSIFIABLE_TYPES = [
    EntityType.COMMITMENT,
    EntityType.GOAL,
    EntityType.TASK,
    EntityType.VISION,
    EntityType.MILESTONE,
]


class TriageClassification(BaseModel):
    """AI classification result for a triage item."""

    suggested_type: str = Field(
        description="Suggested entity type: commitment, goal, task, vision, or milestone"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    detected_stakeholder: str | None = Field(
        default=None, description="Detected stakeholder if mentioned"
    )
    detected_date: str | None = Field(
        default=None, description="Detected date or deadline if mentioned"
    )
    reasoning: str = Field(description="Brief explanation of the classification")


class ClarifyingQuestion(BaseModel):
    """Question to ask when classification confidence is low."""

    question: str = Field(description="The clarifying question to ask the user")


@dataclass
class TriageAnalysis:
    """Result from analyzing a triage item.

    Attributes:
        raw_text: The original captured text.
        classification: The AI classification result (if confident).
        question: Clarifying question (if confidence is low).
        is_confident: Whether the AI is confident in its classification.
    """

    raw_text: str
    classification: TriageClassification | None
    question: ClarifyingQuestion | None

    @property
    def is_confident(self) -> bool:
        """Check if AI is confident in classification.

        Returns:
            True if classification exists and confidence >= 0.7.
        """
        if self.classification is None:
            return False
        return self.classification.confidence >= CONFIDENCE_THRESHOLD

    @property
    def suggested_entity_type(self) -> EntityType | None:
        """Get the suggested EntityType enum value.

        Returns:
            EntityType enum if classification is confident, None otherwise.
        """
        if not self.is_confident or self.classification is None:
            return None
        try:
            return EntityType(self.classification.suggested_type)
        except ValueError:
            return None


# System prompt for triage classification
TRIAGE_SYSTEM_PROMPT = """\
You are a classification assistant for a personal commitment tracking system.

Your job is to analyze captured text and classify it into one of these entity types:

1. **commitment** - A promise to deliver something to someone by a specific date
   - Has a deliverable (what), stakeholder (who), and due date (when)
   - Example: "Send quarterly report to Sarah by Friday"

2. **goal** - A larger objective that commitments work toward
   - Has a problem statement and solution vision
   - Example: "Improve team communication" or "Launch new product by Q3"

3. **task** - A specific action item, usually part of a commitment
   - Concrete, actionable step
   - Example: "Review pull request" or "Update documentation"

4. **vision** - A long-term aspiration or ideal future state
   - Describes where you want to be, not specific actions
   - Example: "Become a thought leader in AI" or "Build a sustainable business"

5. **milestone** - A checkpoint or target date for progress on a goal
   - Has a target date and marks progress
   - Example: "Complete MVP by March" or "Reach 1000 users"

Guidelines:
- If the text mentions delivering something TO someone BY a date, it's likely a commitment
- If the text is vague or aspirational without specifics, it may be a vision or goal
- If the text is a simple action item, it's likely a task
- Extract any stakeholder names or dates mentioned
- If you're unsure, ask a clarifying question instead

Confidence levels:
- 0.9-1.0: Very clear classification with explicit markers
- 0.7-0.9: Good fit but some ambiguity
- Below 0.7: Ask a clarifying question instead of guessing
"""


def _get_triage_agent() -> Agent[None, TriageClassification | ClarifyingQuestion]:
    """Create a PydanticAI agent for triage classification.

    Returns:
        Configured agent with structured output.
    """
    settings = get_settings()
    model = f"{settings.ai_provider}:{settings.ai_model}"

    return Agent(
        model,
        output_type=[TriageClassification, ClarifyingQuestion],
        system_prompt=TRIAGE_SYSTEM_PROMPT,
    )


def classify_triage_item(text: str) -> TriageAnalysis:
    """Classify a captured text item into an entity type.

    Uses AI to analyze the text and suggest an appropriate entity type
    (commitment, goal, task, vision, or milestone).

    Args:
        text: The raw captured text to classify.

    Returns:
        TriageAnalysis with classification or clarifying question.

    Raises:
        TimeoutError: If AI call exceeds timeout.
    """
    agent = _get_triage_agent()

    prompt = f"Classify this captured text:\n\n{text}"

    # Wrap sync AI call with timeout via ThreadPoolExecutor
    result = run_sync_with_timeout(agent.run_sync, prompt, timeout=AI_TIMEOUT_SECONDS)
    output = result.output

    if isinstance(output, TriageClassification):
        # Check confidence threshold
        if output.confidence >= CONFIDENCE_THRESHOLD:
            return TriageAnalysis(
                raw_text=text,
                classification=output,
                question=None,
            )
        # Low confidence - generate a clarifying question
        return TriageAnalysis(
            raw_text=text,
            classification=output,
            question=ClarifyingQuestion(
                question=f"I'm not sure about this one. {output.reasoning} "
                f"Is this a {output.suggested_type}, or something else?"
            ),
        )
    # AI returned a clarifying question directly
    return TriageAnalysis(
        raw_text=text,
        classification=None,
        question=output,
    )


async def classify_triage_item_async(text: str) -> TriageAnalysis:
    """Async version of classify_triage_item.

    Args:
        text: The raw captured text to classify.

    Returns:
        TriageAnalysis with classification or clarifying question.

    Raises:
        TimeoutError: If AI call exceeds timeout.
    """
    agent = _get_triage_agent()

    prompt = f"Classify this captured text:\n\n{text}"

    # Wrap async AI call with timeout
    result = await with_ai_timeout(agent.run(prompt))
    output = result.output

    if isinstance(output, TriageClassification):
        if output.confidence >= CONFIDENCE_THRESHOLD:
            return TriageAnalysis(
                raw_text=text,
                classification=output,
                question=None,
            )
        return TriageAnalysis(
            raw_text=text,
            classification=output,
            question=ClarifyingQuestion(
                question=f"I'm not sure about this one. {output.reasoning} "
                f"Is this a {output.suggested_type}, or something else?"
            ),
        )
    return TriageAnalysis(
        raw_text=text,
        classification=None,
        question=output,
    )
