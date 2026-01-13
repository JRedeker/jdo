"""Commitment command handler implementations.

Includes handlers for commit, at-risk, cleanup, recover, and abandon operations
that implement the Honor-Your-Word protocol.
"""

from __future__ import annotations

from typing import Any

from jdo.commands.handlers.base import CommandHandler, HandlerResult
from jdo.commands.parser import ParsedCommand
from jdo.db.persistence import PersistenceService
from jdo.db.session import get_session
from jdo.integrity import IntegrityService


class CommitHandler(CommandHandler):
    """Handler for /commit command - creates commitments.

    Stateless handler - draft data flows through HandlerResult.draft_data
    and is tracked by Session.pending_draft.
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /commit command.

        Args:
            cmd: The parsed command.
            context: Context with conversation and extracted data.

        Returns:
            HandlerResult with draft panel and message.
        """
        # Check for pre-extracted data
        extracted = context.get("extracted", {})

        # Try to extract from conversation if not pre-extracted
        if not extracted and context.get("conversation"):
            extracted = self._extract_from_conversation(context["conversation"])

        # Build draft data
        draft_data = {
            "deliverable": extracted.get("deliverable", ""),
            "stakeholder": extracted.get("stakeholder", ""),
            "due_date": extracted.get("due_date"),
            "due_time": extracted.get("due_time"),
            "goal_id": extracted.get("goal_id"),
            "milestone_id": extracted.get("milestone_id"),
        }

        # Check for missing required fields
        missing_fields = []
        if not draft_data["deliverable"]:
            missing_fields.append("deliverable")
        if not draft_data["stakeholder"]:
            missing_fields.append("stakeholder")
        if not draft_data["due_date"]:
            missing_fields.append("due_date")

        # Build response message
        if missing_fields:
            message = self._build_prompt_message(missing_fields, draft_data)
            needs_confirmation = False
        else:
            # Get velocity for confirmation message
            try:
                with get_session() as session:
                    service = PersistenceService(session)
                    created, completed = service.get_commitment_velocity()
            except Exception:  # noqa: BLE001
                # If database queries fail, proceed without guardrails
                created = 0
                completed = 0

            message = self._build_confirmation_message(draft_data, created, completed)
            needs_confirmation = True

        return HandlerResult(
            message=message,
            panel_update={
                "mode": "draft",
                "entity_type": "commitment",
                "data": draft_data,
            },
            draft_data=draft_data,
            needs_confirmation=needs_confirmation,
        )

    def _extract_from_conversation(self, conversation: list[dict[str, Any]]) -> dict[str, Any]:
        """Extract commitment fields from conversation.

        Args:
            conversation: List of conversation messages.

        Returns:
            Dict with extracted fields.
        """
        # Simple placeholder extraction - real implementation uses AI
        extracted: dict[str, Any] = {}

        for msg in conversation:
            if msg.get("role") == "user":
                content = msg.get("content", "").lower()
                # Basic keyword detection (placeholder for AI)
                if "send" in content or "deliver" in content or "report" in content:
                    extracted["deliverable"] = msg.get("content", "")[:100]

        return extracted

    def _build_prompt_message(self, missing_fields: list[str], draft_data: dict[str, Any]) -> str:  # noqa: ARG002
        """Build a message prompting for missing fields.

        Args:
            missing_fields: List of field names that are missing.
            draft_data: Current draft data.

        Returns:
            Message prompting for missing information.
        """
        prompts = []

        if "deliverable" in missing_fields:
            prompts.append("What will you deliver?")
        if "stakeholder" in missing_fields:
            prompts.append("Who are you making this commitment to?")
        if "due_date" in missing_fields:
            prompts.append("When is it due?")

        return "I need a bit more information to create this commitment. " + " ".join(prompts)

    def _build_confirmation_message(
        self,
        draft_data: dict[str, Any],
        velocity_created: int,
        velocity_completed: int,
    ) -> str:
        """Build confirmation message with optional velocity coaching.

        Args:
            draft_data: The draft commitment data.
            velocity_created: Commitments created in past week.
            velocity_completed: Commitments completed in past week.

        Returns:
            Message asking for confirmation with optional coaching notes.
        """
        lines = ["Here's the commitment I'll create:", ""]
        lines.append(f"  Deliverable: {draft_data['deliverable']}")
        lines.append(f"  Stakeholder: {draft_data['stakeholder']}")
        due_time = draft_data.get("due_time")
        due_str = f"  Due: {draft_data['due_date']}"
        if due_time:
            due_str += f" {due_time}"
        lines.append(due_str)

        # Add velocity warning if creating faster than completing
        if velocity_created > velocity_completed:
            lines.append("")
            lines.append(
                f"**Note**: You've created {velocity_created} commitments this week "
                f"but only completed {velocity_completed}. Are you overcommitting?"
            )

        lines.append("")
        lines.append("Does this look right? (yes to confirm, or tell me what to change)")

        return "\n".join(lines)


class AtRiskHandler(CommandHandler):
    """Handler for /atrisk command - marks commitment as at-risk.

    Starts the Honor-Your-Word protocol: notify stakeholders, clean up impact.
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /atrisk command.

        Args:
            cmd: The parsed command.
            context: Context with current commitment data.

        Returns:
            HandlerResult for at-risk workflow.
        """
        current_commitment = context.get("current_commitment")
        available_commitments = context.get("available_commitments", [])

        # Check if we have a commitment in context
        if not current_commitment:
            if available_commitments:
                return self._prompt_for_commitment_selection(available_commitments)
            return HandlerResult(
                message=(
                    "No active commitments to mark as at-risk. "
                    "Create a commitment first with /commit."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Check if already at-risk
        status = current_commitment.get("status", "")
        if status == "at_risk":
            return HandlerResult(
                message=(
                    "This commitment is already marked at-risk. "
                    "Would you like to view the cleanup plan? Use /cleanup."
                ),
                panel_update={
                    "mode": "view",
                    "entity_type": "commitment",
                    "data": current_commitment,
                },
                draft_data=None,
                needs_confirmation=False,
            )

        # Check if commitment is completable (not already completed/abandoned)
        if status in ("completed", "abandoned"):
            return HandlerResult(
                message=(
                    f"This commitment is already {status}. "
                    "Only pending or in-progress commitments can be marked at-risk."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Start at-risk workflow - prompt for reason
        deliverable = current_commitment.get("deliverable") or "this commitment"
        stakeholder = current_commitment.get("stakeholder_name") or "the stakeholder"

        return HandlerResult(
            message=(
                f"You're about to mark '{deliverable}' as at-risk.\n\n"
                "Why might you miss this commitment? "
                "(This helps draft the notification to the stakeholder)"
            ),
            panel_update={
                "mode": "atrisk_workflow",
                "entity_type": "commitment",
                "data": current_commitment,
                "workflow_step": "reason",
            },
            draft_data={
                "commitment_id": current_commitment.get("id"),
                "stakeholder_name": stakeholder,
                "reason": None,
                "impact": None,
                "proposed_resolution": None,
            },
            needs_confirmation=False,
        )

    def _prompt_for_commitment_selection(self, commitments: list[dict[str, Any]]) -> HandlerResult:
        """Prompt user to select which commitment is at-risk."""
        # Filter to only active commitments
        active = [c for c in commitments if c.get("status") in ("pending", "in_progress")]

        if not active:
            return HandlerResult(
                message=(
                    "No active commitments to mark as at-risk. "
                    "All your commitments are either completed or abandoned."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        lines = ["Which commitment is at risk?", ""]
        for i, c in enumerate(active, 1):
            deliverable = (c.get("deliverable") or "Untitled")[:50]
            due = c.get("due_date") or "No date"
            lines.append(f"  {i}. {deliverable} (due: {due})")
        lines.append("")
        lines.append("Enter a number to select, or describe the commitment.")

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "list",
                "entity_type": "commitment",
                "items": active,
            },
            draft_data=None,
            needs_confirmation=False,
        )


class CleanupHandler(CommandHandler):
    """Handler for /cleanup command - view or update cleanup plan."""

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /cleanup command.

        Args:
            cmd: The parsed command.
            context: Context with current commitment and cleanup plan data.

        Returns:
            HandlerResult with cleanup plan view or prompt.
        """
        current_commitment = context.get("current_commitment")
        cleanup_plan = context.get("cleanup_plan")

        # Check for commitment context
        if not current_commitment:
            return HandlerResult(
                message=(
                    "Select a commitment first to view its cleanup plan. "
                    "Use /show commitments to see your commitments."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        status = current_commitment.get("status", "")

        # Check if commitment has a cleanup plan
        if not cleanup_plan:
            if status == "at_risk":
                # At-risk but no cleanup plan - shouldn't happen but handle gracefully
                return HandlerResult(
                    message=(
                        "This commitment is at-risk but has no cleanup plan. "
                        "This may indicate a data issue. Please try /atrisk again."
                    ),
                    panel_update=None,
                    draft_data=None,
                    needs_confirmation=False,
                )
            # Not at-risk, no cleanup plan
            return HandlerResult(
                message=(
                    "This commitment doesn't have a cleanup plan. "
                    "Would you like to mark it as at-risk? Use /atrisk."
                ),
                panel_update={
                    "mode": "view",
                    "entity_type": "commitment",
                    "data": current_commitment,
                },
                draft_data=None,
                needs_confirmation=False,
            )

        # Show cleanup plan
        return self._show_cleanup_plan(current_commitment, cleanup_plan)

    def _show_cleanup_plan(
        self, commitment: dict[str, Any], cleanup_plan: dict[str, Any]
    ) -> HandlerResult:
        """Display cleanup plan details."""
        plan_status = cleanup_plan.get("status", "unknown")
        impact = cleanup_plan.get("impact_description") or "Not specified"
        actions = cleanup_plan.get("mitigation_actions", [])
        notification_complete = cleanup_plan.get("notification_task_completed", False)

        lines = [
            "Cleanup Plan",
            "=" * 40,
            "",
            f"Status: {plan_status}",
            f"Notification sent: {'Yes' if notification_complete else 'No'}",
            "",
            "Impact Description:",
            f"  {impact}",
            "",
            "Mitigation Actions:",
        ]

        if actions:
            for i, action in enumerate(actions, 1):
                lines.append(f"  {i}. {action}")
        else:
            lines.append("  (No mitigation actions defined yet)")

        lines.extend(
            [
                "",
                "You can update this plan by describing changes in the chat.",
                "Example: 'Add mitigation action: follow up weekly until resolved'",
            ]
        )

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "cleanup",
                "entity_type": "cleanup_plan",
                "data": cleanup_plan,
                "commitment": commitment,
            },
            draft_data=None,
            needs_confirmation=False,
        )


class AbandonHandler(CommandHandler):
    """Handler for /abandon command - marks commitment as abandoned.

    Implements soft enforcement per Honor-Your-Word protocol:
    - If commitment is at_risk and notification task not completed, warns user
    - Offers option to mark at-risk first if stakeholder exists
    - On confirmed abandon, sets CleanupPlan status to skipped if applicable
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:  # noqa: ARG002
        """Execute /abandon command.

        Args:
            cmd: The parsed command.
            context: Context with current commitment data.

        Returns:
            HandlerResult with appropriate prompt or confirmation.
        """
        current_commitment = context.get("current_commitment")
        available_commitments = context.get("available_commitments", [])

        # Check if we have a commitment in context
        if not current_commitment:
            return self._handle_no_commitment(available_commitments)

        # Check if already completed or abandoned
        validation_result = self._validate_commitment_status(current_commitment)
        if validation_result:
            return validation_result

        status = current_commitment.get("status") or ""
        deliverable = current_commitment.get("deliverable") or "this commitment"
        stakeholder = current_commitment.get("stakeholder_name") or ""

        # Soft enforcement for at-risk commitments
        if status == "at_risk":
            return self._handle_at_risk_abandon(current_commitment, context)

        # Pre-abandon prompt for commitments with stakeholders
        if stakeholder and status in ("pending", "in_progress"):
            return self._prompt_atrisk_first(current_commitment)

        # Standard abandonment (no stakeholder)
        return HandlerResult(
            message=f"Abandon '{deliverable}'?\n\nThis will mark the commitment as abandoned.",
            panel_update={
                "mode": "view",
                "entity_type": "commitment",
                "data": current_commitment,
                "action": "abandon",
            },
            draft_data=None,
            needs_confirmation=True,
        )

    def _handle_no_commitment(self, available_commitments: list[dict[str, Any]]) -> HandlerResult:
        """Handle case when no commitment is in context."""
        if available_commitments:
            return self._prompt_for_commitment_selection(available_commitments)
        return HandlerResult(
            message="No active commitments to abandon. Create a commitment first with /commit.",
            panel_update=None,
            draft_data=None,
            needs_confirmation=False,
        )

    def _validate_commitment_status(self, commitment: dict[str, Any]) -> HandlerResult | None:
        """Validate commitment can be abandoned. Returns error result or None if valid."""
        status = commitment.get("status", "")
        if status == "completed":
            return HandlerResult(
                message=(
                    "This commitment is already completed. "
                    "Completed commitments cannot be abandoned."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )
        if status == "abandoned":
            return HandlerResult(
                message="This commitment is already abandoned.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )
        return None

    def _handle_at_risk_abandon(
        self, commitment: dict[str, Any], context: dict[str, Any]
    ) -> HandlerResult:
        """Handle abandonment of at-risk commitment with soft enforcement."""
        deliverable = commitment.get("deliverable") or "this commitment"
        stakeholder = commitment.get("stakeholder_name") or "the stakeholder"
        cleanup_plan = context.get("cleanup_plan")
        notification_task = context.get("notification_task")

        # Check if notification task exists and is incomplete
        notification_incomplete = False
        if notification_task:
            task_status = notification_task.get("status", "")
            notification_incomplete = task_status not in ("completed", "done")

        if notification_incomplete:
            # Warn user about incomplete notification
            return HandlerResult(
                message=(
                    f"⚠️ You haven't notified {stakeholder} yet.\n\n"
                    f"Abandoning '{deliverable}' without notification will:\n"
                    "• Set your cleanup plan status to 'skipped'\n"
                    "• Negatively affect your integrity score\n\n"
                    "Options:\n"
                    "• Type 'yes' to abandon anyway\n"
                    "• Type 'notify' to complete notification first\n"
                    "• Type 'cancel' to go back"
                ),
                panel_update={
                    "mode": "abandon_warning",
                    "entity_type": "commitment",
                    "data": commitment,
                    "cleanup_plan": cleanup_plan,
                    "notification_task": notification_task,
                    "warning_type": "notification_incomplete",
                },
                draft_data={
                    "commitment_id": commitment.get("id"),
                    "skip_notification": True,
                    "skipped_reason": "User abandoned without completing notification",
                },
                needs_confirmation=True,
            )

        # Notification completed, standard at-risk abandonment
        return HandlerResult(
            message=(
                f"Abandon '{deliverable}'?\n\n"
                f"You've notified {stakeholder}. The commitment will be marked as abandoned "
                "and the cleanup plan completed."
            ),
            panel_update={
                "mode": "view",
                "entity_type": "commitment",
                "data": commitment,
                "action": "abandon",
                "cleanup_plan": cleanup_plan,
            },
            draft_data=None,
            needs_confirmation=True,
        )

    def _prompt_atrisk_first(self, commitment: dict[str, Any]) -> HandlerResult:
        """Prompt user to mark at-risk first before abandoning."""
        deliverable = commitment.get("deliverable") or "this commitment"
        stakeholder = commitment.get("stakeholder_name") or "the stakeholder"

        return HandlerResult(
            message=(
                f"'{deliverable}' has a stakeholder ({stakeholder}).\n\n"
                "Would you like to:\n"
                "• Mark at-risk first to notify them? (recommended)\n"
                "• Abandon directly without notification?\n\n"
                "Type 'atrisk' to mark at-risk first, or 'abandon' to abandon directly."
            ),
            panel_update={
                "mode": "abandon_prompt",
                "entity_type": "commitment",
                "data": commitment,
                "prompt_type": "atrisk_first",
            },
            draft_data={
                "commitment_id": commitment.get("id"),
                "stakeholder_name": stakeholder,
            },
            needs_confirmation=False,
        )

    def _prompt_for_commitment_selection(self, commitments: list[dict[str, Any]]) -> HandlerResult:
        """Prompt user to select which commitment to abandon."""
        # Filter to only active commitments
        active = [
            c for c in commitments if c.get("status") in ("pending", "in_progress", "at_risk")
        ]

        if not active:
            return HandlerResult(
                message=(
                    "No active commitments to abandon. "
                    "All your commitments are either completed or already abandoned."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        lines = ["Which commitment do you want to abandon?", ""]
        for i, c in enumerate(active, 1):
            deliverable = (c.get("deliverable") or "Untitled")[:50]
            status = c.get("status") or "unknown"
            status_indicator = " ⚠️" if status == "at_risk" else ""
            lines.append(f"  {i}. {deliverable} [{status}]{status_indicator}")
        lines.append("")
        lines.append("Enter a number to select, or describe the commitment.")

        return HandlerResult(
            message="\n".join(lines),
            panel_update={
                "mode": "list",
                "entity_type": "commitment",
                "items": active,
            },
            draft_data=None,
            needs_confirmation=False,
        )


class RecoverHandler(CommandHandler):
    """Handler for /recover command - recovers at-risk commitment to in_progress.

    Used when the situation has improved and the commitment can be delivered.
    """

    def execute(self, cmd: ParsedCommand, context: dict[str, Any]) -> HandlerResult:
        """Execute /recover command.

        Args:
            cmd: The parsed command.
            context: Context with current commitment data.

        Returns:
            HandlerResult for recovery workflow.
        """
        current_commitment = context.get("current_commitment")

        # Check if we have a commitment in context
        if not current_commitment:
            return HandlerResult(
                message=(
                    "No commitment selected. Use /show commitments to view "
                    "your commitments, then select one to recover."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Check if commitment is at-risk
        status = current_commitment.get("status", "")
        if hasattr(status, "value"):
            status = status.value

        if status != "at_risk":
            return HandlerResult(
                message=(
                    f"This commitment is not at-risk (current status: {status}). "
                    "Only at-risk commitments can be recovered."
                ),
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        commitment_id = current_commitment.get("id")
        if not commitment_id:
            return HandlerResult(
                message="Could not identify commitment. Please try again.",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )

        # Check for notification_resolved argument
        notification_resolved = False
        if cmd.args and cmd.args[0].lower() in ("resolved", "yes", "y"):
            notification_resolved = True

        try:
            with get_session() as session:
                service = IntegrityService()
                result = service.recover_commitment(
                    session=session,
                    commitment_id=commitment_id,
                    notification_resolved=notification_resolved,
                )

                deliverable = result.commitment.deliverable or "Commitment"
                stakeholder = current_commitment.get("stakeholder_name", "stakeholder")

                if result.notification_still_needed:
                    # Prompt user about notification task
                    message = (
                        f"'{deliverable}' has been recovered to in-progress.\n\n"
                        f"You previously marked this as at-risk. "
                        f"Do you still need to notify {stakeholder}, "
                        "or has the situation resolved?\n\n"
                        "Reply with:\n"
                        "  - '/recover resolved' to skip the notification (situation resolved)\n"
                        "  - Keep the notification task to complete it"
                    )
                else:
                    message = (
                        f"'{deliverable}' has been recovered to in-progress.\n\n"
                        "The cleanup plan has been cancelled. "
                        "Great work getting things back on track!"
                    )

                # Build updated commitment data for panel
                updated_data = dict(current_commitment)
                updated_data["status"] = "in_progress"

                return HandlerResult(
                    message=message,
                    panel_update={
                        "mode": "view",
                        "entity_type": "commitment",
                        "data": updated_data,
                    },
                    draft_data=None,
                    needs_confirmation=False,
                )

        except ValueError as e:
            return HandlerResult(
                message=f"Could not recover commitment: {e}",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )
        except Exception as e:  # noqa: BLE001
            return HandlerResult(
                message=f"An error occurred: {e}",
                panel_update=None,
                draft_data=None,
                needs_confirmation=False,
            )
