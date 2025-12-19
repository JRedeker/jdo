"""Mock-based UAT scenario tests.

These tests use deterministic mock agents for fast, reproducible testing.
They verify the UAT infrastructure works correctly with predefined action sequences.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic_ai import Agent

from jdo.app import JdoApp
from tests.uat.driver import UAT_SYSTEM_PROMPT, AIUATDriver
from tests.uat.loader import load_scenario
from tests.uat.mocks import get_mock_for_scenario
from tests.uat.models import UATAction


@pytest.fixture
def scenarios_path() -> Path:
    """Return path to scenarios directory."""
    return Path(__file__).parent / "scenarios"


class TestNavigationScenario:
    """Test the navigation scenario with mock agent."""

    async def test_navigation_completes(self, uat_app: JdoApp, scenarios_path: Path) -> None:
        """Navigation scenario completes successfully with mock agent."""
        scenario = load_scenario(scenarios_path / "navigation.yaml")
        mock_model = get_mock_for_scenario(scenario.name)
        assert mock_model is not None, "Mock model should exist for navigation"

        agent: Agent[None, UATAction] = Agent(
            mock_model,
            output_type=UATAction,
            system_prompt=UAT_SYSTEM_PROMPT,
        )
        driver = AIUATDriver(uat_app, agent, debug=True)

        async with uat_app.run_test() as pilot:
            result = await driver.run_scenario(scenario, pilot)

        assert result.success, f"Scenario failed: {result.error}"
        assert result.total_steps > 0
        assert "completed" in result.success_criteria_met


class TestIntegrityDashboardScenario:
    """Test the integrity dashboard scenario with mock agent."""

    async def test_integrity_view_completes(self, uat_app: JdoApp, scenarios_path: Path) -> None:
        """Integrity dashboard scenario completes successfully."""
        scenario = load_scenario(scenarios_path / "integrity_dashboard.yaml")
        mock_model = get_mock_for_scenario(scenario.name)
        assert mock_model is not None, "Mock model should exist for integrity_dashboard"

        agent: Agent[None, UATAction] = Agent(
            mock_model,
            output_type=UATAction,
            system_prompt=UAT_SYSTEM_PROMPT,
        )
        driver = AIUATDriver(uat_app, agent, debug=True)

        async with uat_app.run_test() as pilot:
            result = await driver.run_scenario(scenario, pilot)

        assert result.success, f"Scenario failed: {result.error}"
        assert "completed" in result.success_criteria_met


class TestHierarchyScenario:
    """Test the planning hierarchy scenario with mock agent."""

    async def test_hierarchy_view_completes(self, uat_app: JdoApp, scenarios_path: Path) -> None:
        """Planning hierarchy scenario completes successfully."""
        scenario = load_scenario(scenarios_path / "planning_hierarchy.yaml")
        mock_model = get_mock_for_scenario(scenario.name)
        assert mock_model is not None, "Mock model should exist for planning_hierarchy"

        agent: Agent[None, UATAction] = Agent(
            mock_model,
            output_type=UATAction,
            system_prompt=UAT_SYSTEM_PROMPT,
        )
        driver = AIUATDriver(uat_app, agent, debug=True)

        async with uat_app.run_test() as pilot:
            result = await driver.run_scenario(scenario, pilot)

        assert result.success, f"Scenario failed: {result.error}"
        assert "completed" in result.success_criteria_met
