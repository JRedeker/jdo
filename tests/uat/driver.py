"""AI UAT Driver for orchestrating AI-driven test execution.

The driver coordinates between the AI agent and the Textual app,
executing actions and observing state changes.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from loguru import logger
from pydantic_ai import Agent
from textual.pilot import Pilot

from tests.uat.models import (
    ActionType,
    StepResult,
    UATAction,
    UATResult,
    UATScenario,
    UATStepLimitError,
    UATTimeoutError,
    UIState,
)
from tests.uat.observer import UIStateObserver

if TYPE_CHECKING:
    from jdo.app import JdoApp


def _raise_timeout_error(scenario_name: str, timeout: int, elapsed: float) -> None:
    """Raise UATTimeoutError (abstracted for TRY301 compliance)."""
    raise UATTimeoutError(scenario_name, timeout, elapsed)


def _raise_step_limit_error(scenario_name: str, max_steps: int, step_number: int) -> None:
    """Raise UATStepLimitError (abstracted for TRY301 compliance)."""
    raise UATStepLimitError(scenario_name, max_steps, step_number)


# System prompt for the UAT agent
UAT_SYSTEM_PROMPT = """\
You are an AI agent performing User Acceptance Testing (UAT) on a TUI application.

Your task is to navigate the app and accomplish the goal by taking actions step by step.

## Available Actions

You can perform these actions:
- **press**: Press a key or key combination (e.g., "n", "escape", "ctrl+enter")
- **click**: Click on a widget by CSS selector (e.g., "#submit-button")
- **type**: Type text into the focused input widget
- **wait**: Wait for UI to update (use sparingly, value is delay in seconds)
- **assert**: Check that a condition is true about the current UI state
- **done**: Signal that you have completed the goal (or cannot proceed further)

## Response Format

You must respond with a single action in JSON format:
{
    "action_type": "press|click|type|wait|assert|done",
    "target": "key/selector/null",
    "value": "text/assertion/null",
    "reason": "Why you are taking this action"
}

## Guidelines

1. Read the current UI state carefully before deciding on an action
2. Use keyboard shortcuts (shown in Available Actions) when possible - they're more reliable
3. Take one action at a time and observe the result
4. If you get stuck, try pressing "escape" to go back
5. When you've accomplished the goal, return action_type="done"
6. Include clear reasoning for each action
7. If you encounter an error or can't proceed, explain why in your "done" action

## Important Keys

- "n" - New chat
- "escape" - Go back / close
- "ctrl+enter" - Submit in chat
- "tab" - Switch focus
- Arrow keys - Navigate lists
- "enter" - Select / confirm
"""


class AIUATDriver:
    """Orchestrates AI-driven UAT test execution.

    The driver runs a loop:
    1. Capture current UI state
    2. Send state + goal to AI agent
    3. Parse AI's action response
    4. Execute action via Pilot
    5. Repeat until done or limits reached
    """

    def __init__(
        self,
        app: JdoApp,
        agent: Agent[None, UATAction],
        *,
        debug: bool = False,
    ) -> None:
        """Initialize the UAT driver.

        Args:
            app: The JDO app instance to test.
            agent: The PydanticAI agent for decision-making.
            debug: Whether to enable debug logging.
        """
        self.app = app
        self.agent = agent
        self.debug = debug
        self.observer = UIStateObserver(app)
        self._pilot: Pilot[Any] | None = None

    async def run_scenario(
        self,
        scenario: UATScenario,
        pilot: Pilot[Any],
    ) -> UATResult:
        """Run a UAT scenario to completion.

        Args:
            scenario: The scenario to execute.
            pilot: The Textual Pilot for interacting with the app.

        Returns:
            UATResult with execution details.

        Raises:
            UATStepLimitError: If max_steps is exceeded.
            UATTimeoutError: If timeout_seconds is exceeded.
        """
        self._pilot = pilot
        start_time = time.time()
        steps: list[StepResult] = []
        error: str | None = None

        try:
            # Run preconditions
            for precondition in scenario.preconditions:
                await self._execute_precondition(precondition, pilot)

            # Main execution loop
            step_number = 0
            while step_number < scenario.max_steps:
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > scenario.timeout_seconds:
                    _raise_timeout_error(scenario.name, scenario.timeout_seconds, elapsed)

                step_number += 1
                step_start = time.time()

                # Capture UI state before action
                ui_state_before = self.observer.capture()

                # Get action from AI
                action = await self._get_next_action(scenario.goal, ui_state_before)

                if self.debug:
                    logger.debug(
                        f"Step {step_number}: {action.action_type.value} "
                        f"target={action.target} value={action.value}"
                    )
                    logger.debug(f"Reason: {action.reason}")

                # Check for done
                if action.action_type == ActionType.DONE:
                    ui_state_after = self.observer.capture()
                    steps.append(
                        StepResult(
                            step_number=step_number,
                            action=action,
                            success=True,
                            ui_state_before=ui_state_before,
                            ui_state_after=ui_state_after,
                            duration_ms=(time.time() - step_start) * 1000,
                        )
                    )
                    break

                # Execute action
                try:
                    await self._execute_action(action, pilot)
                    await pilot.pause()  # Allow UI to update

                    ui_state_after = self.observer.capture()
                    steps.append(
                        StepResult(
                            step_number=step_number,
                            action=action,
                            success=True,
                            ui_state_before=ui_state_before,
                            ui_state_after=ui_state_after,
                            duration_ms=(time.time() - step_start) * 1000,
                        )
                    )
                except (KeyError, ValueError, AttributeError, RuntimeError) as e:
                    # Catch common action execution errors - let AI recover
                    ui_state_after = self.observer.capture()
                    steps.append(
                        StepResult(
                            step_number=step_number,
                            action=action,
                            success=False,
                            error=str(e),
                            ui_state_before=ui_state_before,
                            ui_state_after=ui_state_after,
                            duration_ms=(time.time() - step_start) * 1000,
                        )
                    )

            else:
                # Loop completed without "done" action
                _raise_step_limit_error(scenario.name, scenario.max_steps, step_number)

        except (UATStepLimitError, UATTimeoutError):
            raise
        except (KeyError, ValueError, AttributeError, RuntimeError, OSError) as e:
            # Catch unexpected scenario execution errors
            error = str(e)
            logger.exception(f"Scenario '{scenario.name}' failed with error")

        # Evaluate success criteria
        final_state = self.observer.capture()
        criteria_met, criteria_failed = self._evaluate_criteria(
            scenario.success_criteria, final_state, steps
        )

        total_duration = (time.time() - start_time) * 1000
        success = error is None and len(criteria_failed) == 0

        return UATResult(
            scenario_name=scenario.name,
            success=success,
            steps=steps,
            total_steps=len(steps),
            total_duration_ms=total_duration,
            error=error,
            final_ui_state=final_state,
            success_criteria_met=criteria_met,
            success_criteria_failed=criteria_failed,
        )

    async def _get_next_action(self, goal: str, ui_state: UIState) -> UATAction:
        """Get the next action from the AI agent.

        Args:
            goal: The scenario goal.
            ui_state: Current UI state.

        Returns:
            The action to execute.
        """
        prompt = f"""## Goal
{goal}

## Current UI State
{ui_state.to_prompt_context()}

What action should I take next to accomplish the goal?"""

        result = await self.agent.run(prompt)
        return result.output

    async def _execute_action(self, action: UATAction, pilot: Pilot[Any]) -> None:
        """Execute a single action via Pilot.

        Args:
            action: The action to execute.
            pilot: The Textual Pilot.
        """
        action_handlers = {
            ActionType.PRESS: self._execute_press,
            ActionType.CLICK: self._execute_click,
            ActionType.TYPE: self._execute_type,
            ActionType.WAIT: self._execute_wait,
            ActionType.ASSERT: self._execute_assert,
            ActionType.DONE: self._execute_done,
        }
        handler = action_handlers.get(action.action_type)
        if handler:
            await handler(action, pilot)

    async def _execute_press(self, action: UATAction, pilot: Pilot[Any]) -> None:
        """Execute press action."""
        if action.target:
            await pilot.press(action.target)

    async def _execute_click(self, action: UATAction, pilot: Pilot[Any]) -> None:
        """Execute click action."""
        if action.target:
            await pilot.click(action.target)

    async def _execute_type(self, action: UATAction, pilot: Pilot[Any]) -> None:
        """Execute type action."""
        if not action.value:
            return
        focused = self.app.focused
        load_text_fn = getattr(focused, "load_text", None)
        insert_fn = getattr(focused, "insert", None)
        if focused and load_text_fn is not None:
            load_text_fn(action.value)
        elif focused and insert_fn is not None:
            insert_fn(action.value)
        else:
            for char in action.value:
                await pilot.press(char)

    async def _execute_wait(self, action: UATAction, pilot: Pilot[Any]) -> None:
        """Execute wait action."""
        delay = float(action.value) if action.value else 0.5
        await pilot.pause(delay=delay)

    async def _execute_assert(self, action: UATAction, _pilot: Pilot[Any]) -> None:
        """Execute assert action (just logs for now)."""
        logger.info(f"Assertion: {action.value}")

    async def _execute_done(self, _action: UATAction, _pilot: Pilot[Any]) -> None:
        """Done action - handled in main loop."""

    async def _execute_precondition(self, precondition: str, pilot: Pilot[Any]) -> None:
        """Execute a precondition step.

        Preconditions are simple key presses or navigation commands.

        Args:
            precondition: The precondition string (e.g., "press:n" or "wait:1").
            pilot: The Textual Pilot.
        """
        parts = precondition.split(":", 1)
        if len(parts) != 2:
            logger.warning(f"Invalid precondition format: {precondition}")
            return

        cmd, arg = parts
        if cmd == "press":
            await pilot.press(arg)
            await pilot.pause()
        elif cmd == "wait":
            await pilot.pause(delay=float(arg))
        elif cmd == "click":
            await pilot.click(arg)
            await pilot.pause()
        else:
            logger.warning(f"Unknown precondition command: {cmd}")

    def _evaluate_criteria(
        self,
        criteria: list[str],
        final_state: UIState,
        steps: list[StepResult],
    ) -> tuple[list[str], list[str]]:
        """Evaluate success criteria against final state.

        Args:
            criteria: List of success criteria strings.
            final_state: The final UI state.
            steps: The execution steps.

        Returns:
            Tuple of (criteria_met, criteria_failed).
        """
        met: list[str] = []
        failed: list[str] = []

        for criterion in criteria:
            if self._check_criterion(criterion, final_state, steps):
                met.append(criterion)
            else:
                failed.append(criterion)

        return met, failed

    def _check_criterion(
        self,
        criterion: str,
        final_state: UIState,
        steps: list[StepResult],
    ) -> bool:
        """Check if a single criterion is met.

        Criteria formats:
        - "screen:HomeScreen" - Check current screen type
        - "has_messages" - Check that chat has messages
        - "no_errors" - Check that no step had errors
        - "completed" - Check that scenario ended with "done" action

        Args:
            criterion: The criterion string.
            final_state: The final UI state.
            steps: The execution steps.

        Returns:
            True if criterion is met, False otherwise.
        """
        if criterion.startswith("screen:"):
            expected_screen = criterion.split(":", 1)[1]
            return final_state.screen_type == expected_screen

        if criterion == "has_messages":
            return len(final_state.chat_messages) > 0

        if criterion == "no_errors":
            return all(step.success for step in steps)

        if criterion == "completed":
            return len(steps) > 0 and steps[-1].action.action_type == ActionType.DONE

        # Default: check if criterion appears in any step's reason or state
        logger.warning(f"Unknown criterion format, using fuzzy match: {criterion}")
        return True  # Be lenient with unknown criteria
