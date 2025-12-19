"""Mock agent implementations for deterministic UAT testing.

Provides FunctionModel implementations that return predefined action
sequences for each scenario, enabling fast, reproducible tests.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai import ModelResponse
from pydantic_ai.messages import ModelMessage, TextPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from tests.uat.models import ActionType, UATAction


def create_navigation_mock() -> FunctionModel:
    """Create a mock that navigates through screens.

    Returns actions: home -> chat -> home -> settings -> home -> done
    """
    step = 0

    def model_fn(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal step
        step += 1

        actions = [
            # Step 1: Go to chat
            UATAction(
                action_type=ActionType.PRESS,
                target="n",
                reason="Press 'n' to open new chat from home screen",
            ),
            # Step 2: Return to home
            UATAction(
                action_type=ActionType.PRESS,
                target="escape",
                reason="Press escape to return to home screen",
            ),
            # Step 3: Go to settings
            UATAction(
                action_type=ActionType.PRESS,
                target="s",
                reason="Press 's' to open settings",
            ),
            # Step 4: Return to home
            UATAction(
                action_type=ActionType.PRESS,
                target="escape",
                reason="Press escape to return to home screen",
            ),
            # Step 5: Done
            UATAction(
                action_type=ActionType.DONE,
                reason="Successfully navigated through all screens, returning to home",
            ),
        ]

        idx = min(step - 1, len(actions) - 1)
        action = actions[idx]
        return ModelResponse(parts=[TextPart(content=action.model_dump_json())])

    return FunctionModel(model_fn)


def create_commitment_creation_mock() -> FunctionModel:
    """Create a mock that creates a commitment via chat.

    Returns actions for typing a commitment and confirming.
    """
    step = 0

    def model_fn(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal step
        step += 1

        actions = [
            # Already on chat from precondition
            # Step 1: Type commitment text
            UATAction(
                action_type=ActionType.TYPE,
                value="I need to finish the quarterly report by next Friday",
                reason="Type the commitment description into the prompt",
            ),
            # Step 2: Submit
            UATAction(
                action_type=ActionType.PRESS,
                target="ctrl+enter",
                reason="Submit the message with ctrl+enter",
            ),
            # Step 3: Wait for response
            UATAction(
                action_type=ActionType.WAIT,
                value="2",
                reason="Wait for AI to process and respond",
            ),
            # Step 4: Confirm if prompted (type yes)
            UATAction(
                action_type=ActionType.TYPE,
                value="yes",
                reason="Confirm the commitment creation",
            ),
            # Step 5: Submit confirmation
            UATAction(
                action_type=ActionType.PRESS,
                target="ctrl+enter",
                reason="Submit confirmation",
            ),
            # Step 6: Wait
            UATAction(
                action_type=ActionType.WAIT,
                value="1",
                reason="Wait for confirmation to process",
            ),
            # Step 7: Return home
            UATAction(
                action_type=ActionType.PRESS,
                target="escape",
                reason="Return to home screen",
            ),
            # Step 8: Done
            UATAction(
                action_type=ActionType.DONE,
                reason="Commitment creation flow completed",
            ),
        ]

        idx = min(step - 1, len(actions) - 1)
        action = actions[idx]
        return ModelResponse(parts=[TextPart(content=action.model_dump_json())])

    return FunctionModel(model_fn)


def create_integrity_dashboard_mock() -> FunctionModel:
    """Create a mock for viewing integrity dashboard.

    Returns actions: press i -> view -> escape -> done
    """
    step = 0

    def model_fn(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal step
        step += 1

        actions = [
            # Step 1: Open integrity view
            UATAction(
                action_type=ActionType.PRESS,
                target="i",
                reason="Press 'i' to open integrity dashboard",
            ),
            # Step 2: Wait to view
            UATAction(
                action_type=ActionType.WAIT,
                value="1",
                reason="View the integrity metrics",
            ),
            # Step 3: Return home
            UATAction(
                action_type=ActionType.PRESS,
                target="escape",
                reason="Press escape to return to home",
            ),
            # Step 4: Done
            UATAction(
                action_type=ActionType.DONE,
                reason="Successfully viewed integrity dashboard",
            ),
        ]

        idx = min(step - 1, len(actions) - 1)
        action = actions[idx]
        return ModelResponse(parts=[TextPart(content=action.model_dump_json())])

    return FunctionModel(model_fn)


def create_hierarchy_view_mock() -> FunctionModel:
    """Create a mock for viewing planning hierarchy.

    Returns actions: press h -> view -> escape -> done
    """
    step = 0

    def model_fn(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        nonlocal step
        step += 1

        actions = [
            # Step 1: Open hierarchy view
            UATAction(
                action_type=ActionType.PRESS,
                target="h",
                reason="Press 'h' to open hierarchy view",
            ),
            # Step 2: Wait to view
            UATAction(
                action_type=ActionType.WAIT,
                value="1",
                reason="View the planning hierarchy",
            ),
            # Step 3: Return home
            UATAction(
                action_type=ActionType.PRESS,
                target="escape",
                reason="Press escape to return to home",
            ),
            # Step 4: Done
            UATAction(
                action_type=ActionType.DONE,
                reason="Successfully viewed planning hierarchy",
            ),
        ]

        idx = min(step - 1, len(actions) - 1)
        action = actions[idx]
        return ModelResponse(parts=[TextPart(content=action.model_dump_json())])

    return FunctionModel(model_fn)


# Map scenario names to mock creators
SCENARIO_MOCKS = {
    "navigation": create_navigation_mock,
    "commitment_creation": create_commitment_creation_mock,
    "integrity_dashboard": create_integrity_dashboard_mock,
    "planning_hierarchy": create_hierarchy_view_mock,
}


def get_mock_for_scenario(scenario_name: str) -> FunctionModel | None:
    """Get the appropriate mock model for a scenario.

    Args:
        scenario_name: Name of the scenario.

    Returns:
        FunctionModel for the scenario, or None if no mock exists.
    """
    creator = SCENARIO_MOCKS.get(scenario_name)
    if creator:
        return creator()
    return None
