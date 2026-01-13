"""Rich output formatters for Triage Workflow.

Provides formatting for triage items, analysis results, and progress indicators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.console import Group
from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from jdo.ai.triage import TriageAnalysis
    from jdo.models.draft import Draft

# Confidence level thresholds
CONFIDENCE_HIGH = 0.9
CONFIDENCE_MEDIUM = 0.7

# Entity type colors
ENTITY_TYPE_COLORS: dict[str, str] = {
    "commitment": "blue",
    "goal": "green",
    "task": "cyan",
    "vision": "magenta",
    "milestone": "yellow",
    "unknown": "dim",
}


def get_entity_type_color(entity_type: str) -> str:
    """Get the color for an entity type.

    Args:
        entity_type: The entity type string.

    Returns:
        The Rich color name.
    """
    return ENTITY_TYPE_COLORS.get(entity_type.lower(), "default")


def format_confidence(confidence: float) -> Text:
    """Format a confidence score with color coding.

    Args:
        confidence: Confidence score (0.0-1.0).

    Returns:
        Rich Text with colored confidence percentage.
    """
    pct = confidence * 100
    if confidence >= CONFIDENCE_HIGH:
        color = "green"
        label = "High"
    elif confidence >= CONFIDENCE_MEDIUM:
        color = "yellow"
        label = "Medium"
    else:
        color = "red"
        label = "Low"

    result = Text()
    result.append(f"{pct:.0f}%", style=f"bold {color}")
    result.append(f" ({label})", style="dim")
    return result


def format_triage_progress(current: int, total: int) -> Text:
    """Format a triage progress indicator.

    Args:
        current: Current item number (1-based).
        total: Total number of items.

    Returns:
        Rich Text with progress indicator.
    """
    result = Text()
    result.append("Item ", style="dim")
    result.append(str(current), style="bold")
    result.append(" of ", style="dim")
    result.append(str(total), style="bold")
    return result


def format_triage_item(
    draft: Draft,
    analysis: TriageAnalysis | None = None,
    current: int = 1,
    total: int = 1,
) -> Panel:
    """Format a triage item for display.

    Args:
        draft: The draft item being triaged.
        analysis: Optional AI analysis result.
        current: Current item number (1-based).
        total: Total number of items.

    Returns:
        Rich Panel with triage item and analysis.
    """
    parts: list[Any] = []

    # Progress indicator
    progress = format_triage_progress(current, total)
    parts.append(progress)
    parts.append(Text(""))  # Spacer

    # Original text
    parts.append(Text("Captured text:", style="bold"))
    text_content = Text()
    raw_text = draft.partial_data.get("raw_text", "")
    text_content.append(f'"{raw_text}"', style="italic")
    parts.append(text_content)
    parts.append(Text(""))  # Spacer

    # Analysis results (if available)
    if analysis:
        parts.extend(_format_analysis_section(analysis))
    else:
        parts.append(Text("Analyzing...", style="dim italic"))

    # Action options
    parts.append(Text(""))  # Spacer
    parts.append(_format_action_options(analysis))

    return Panel(
        Group(*parts),
        title="[bold]Triage[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )


def _format_analysis_section(analysis: TriageAnalysis) -> list[Any]:
    """Format the analysis section of a triage item.

    Args:
        analysis: The AI analysis result.

    Returns:
        List of renderables for the analysis section.
    """
    parts: list[Any] = []

    if analysis.classification:
        classification = analysis.classification
        parts.append(Text("AI Analysis:", style="bold"))

        # Suggested type with color
        type_color = get_entity_type_color(classification.suggested_type)
        type_line = Text()
        type_line.append("  Type: ", style="dim")
        type_line.append(classification.suggested_type.title(), style=f"bold {type_color}")
        parts.append(type_line)

        # Confidence
        conf_line = Text()
        conf_line.append("  Confidence: ", style="dim")
        conf_line.append_text(format_confidence(classification.confidence))
        parts.append(conf_line)

        # Reasoning
        reason_line = Text()
        reason_line.append("  Reasoning: ", style="dim")
        reason_line.append(classification.reasoning, style="italic")
        parts.append(reason_line)

        # Detected fields
        if classification.detected_stakeholder:
            stakeholder_line = Text()
            stakeholder_line.append("  Stakeholder: ", style="dim")
            stakeholder_line.append(classification.detected_stakeholder)
            parts.append(stakeholder_line)

        if classification.detected_date:
            date_line = Text()
            date_line.append("  Date: ", style="dim")
            date_line.append(classification.detected_date)
            parts.append(date_line)

    # Clarifying question (if needed)
    if analysis.question:
        parts.append(Text(""))  # Spacer
        question_text = Text()
        question_text.append("Question: ", style="bold yellow")
        question_text.append(analysis.question.question, style="yellow")
        parts.append(question_text)

    return parts


def _format_action_options(analysis: TriageAnalysis | None) -> Text:
    """Format the action options for a triage item.

    Args:
        analysis: Optional AI analysis result.

    Returns:
        Rich Text with action options.
    """
    options = Text()
    options.append("Options: ", style="bold")

    if analysis and analysis.is_confident:
        # Confident classification - offer to accept
        options.append("[y]", style="bold green")
        options.append(" Accept  ")
        options.append("[n]", style="bold red")
        options.append(" Reject  ")
        options.append("[c]", style="bold yellow")
        options.append(" Change type  ")
        options.append("[s]", style="bold dim")
        options.append(" Skip  ")
        options.append("[q]", style="bold dim")
        options.append(" Quit")
    elif analysis and analysis.question:
        # Low confidence - need user input
        options.append("[1-5]", style="bold cyan")
        options.append(" Select type  ")
        options.append("[s]", style="bold dim")
        options.append(" Skip  ")
        options.append("[q]", style="bold dim")
        options.append(" Quit")
    else:
        # Still analyzing
        options.append("Waiting for analysis...", style="dim")

    return options


def format_triage_summary(processed: int, total: int, created: dict[str, int]) -> Panel:
    """Format a summary of triage session results.

    Args:
        processed: Number of items processed.
        total: Total number of items.
        created: Dict mapping entity type to count created.

    Returns:
        Rich Panel with triage summary.
    """
    parts: list[Any] = []

    # Header
    parts.append(Text("Triage Complete!", style="bold green"))
    parts.append(Text(""))  # Spacer

    # Stats
    stats = Text()
    stats.append(f"Processed {processed} of {total} items")
    parts.append(stats)
    parts.append(Text(""))  # Spacer

    # Created entities breakdown
    if created:
        parts.append(Text("Created:", style="bold"))
        for entity_type, count in created.items():
            if count > 0:
                type_color = get_entity_type_color(entity_type)
                line = Text()
                line.append(f"  {count} ", style="bold")
                line.append(entity_type, style=type_color)
                line.append("(s)" if count > 1 else "")
                parts.append(line)
    else:
        parts.append(Text("No items created", style="dim"))

    return Panel(
        Group(*parts),
        title="[bold]Triage Summary[/bold]",
        border_style="green",
        padding=(1, 2),
    )


def format_triage_item_plain(draft: Draft, analysis: TriageAnalysis | None = None) -> str:
    """Format a triage item as plain text for AI tools.

    Args:
        draft: The draft item being triaged.
        analysis: Optional AI analysis result.

    Returns:
        Plain text representation.
    """
    raw_text = draft.partial_data.get("raw_text", "")
    lines = [
        "Triage Item",
        "=" * 20,
        "",
        f'Text: "{raw_text}"',
        "",
    ]

    if analysis and analysis.classification:
        classification = analysis.classification
        lines.extend(
            [
                "AI Analysis:",
                f"  Suggested type: {classification.suggested_type}",
                f"  Confidence: {classification.confidence * 100:.0f}%",
                f"  Reasoning: {classification.reasoning}",
            ]
        )

        if classification.detected_stakeholder:
            lines.append(f"  Stakeholder: {classification.detected_stakeholder}")
        if classification.detected_date:
            lines.append(f"  Date: {classification.detected_date}")

    if analysis and analysis.question:
        lines.extend(["", f"Question: {analysis.question.question}"])

    return "\n".join(lines)


def format_triage_queue_status(count: int) -> str:
    """Format a triage queue status message.

    Args:
        count: Number of items in the triage queue.

    Returns:
        Status message string.
    """
    if count == 0:
        return "No items to triage"
    if count == 1:
        return "1 item needs triage"
    return f"{count} items need triage"
