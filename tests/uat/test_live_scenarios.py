"""Live AI-driven UAT scenario tests.

These tests use real AI to drive the application, providing realistic
end-to-end testing. They require valid API credentials and are slower
and more expensive than mock tests.

Run with: pytest tests/uat/test_live_scenarios.py -v -s -m live_ai
Skip with: pytest tests/uat/ -m "not live_ai"
"""

from __future__ import annotations

from pathlib import Path

import pytest
from loguru import logger
from pydantic_ai import Agent

from jdo.app import JdoApp
from jdo.config.settings import get_settings
from tests.uat.conftest import has_ai_credentials
from tests.uat.driver import UAT_SYSTEM_PROMPT, AIUATDriver
from tests.uat.loader import load_scenario
from tests.uat.models import UATAction, UATResult

# Skip all tests in this module if no credentials
pytestmark = [
    pytest.mark.live_ai,
    pytest.mark.skipif(
        not has_ai_credentials(),
        reason="No AI credentials available",
    ),
]


@pytest.fixture
def scenarios_path() -> Path:
    """Return path to scenarios directory."""
    return Path(__file__).parent / "scenarios"


@pytest.fixture
def live_agent() -> Agent[None, UATAction]:
    """Create a live AI agent for UAT testing."""
    settings = get_settings()
    model_id = f"{settings.ai_provider}:{settings.ai_model}"

    return Agent(
        model_id,
        output_type=UATAction,
        system_prompt=UAT_SYSTEM_PROMPT,
    )


def _log_result(result: UATResult) -> None:
    """Log UAT result for debugging."""
    logger.info(f"Scenario: {result.scenario_name}")
    logger.info(f"Success: {result.success}")
    logger.info(f"Steps: {result.total_steps}")
    logger.info(f"Duration: {result.total_duration_ms:.0f}ms")
    if result.error:
        logger.error(f"Error: {result.error}")
    logger.info(f"Criteria met: {result.success_criteria_met}")
    logger.info(f"Criteria failed: {result.success_criteria_failed}")


class TestLiveNavigationScenario:
    """Test navigation with live AI."""

    async def test_live_navigation(
        self,
        live_uat_app: JdoApp,
        live_agent: Agent[None, UATAction],
        scenarios_path: Path,
    ) -> None:
        """Live AI can navigate through the app screens."""
        scenario = load_scenario(scenarios_path / "navigation.yaml")
        driver = AIUATDriver(live_uat_app, live_agent, debug=True)

        async with live_uat_app.run_test() as pilot:
            result = await driver.run_scenario(scenario, pilot)

        _log_result(result)

        for step in result.steps:
            logger.debug(
                f"Step {step.step_number}: {step.action.action_type.value} "
                f"-> {'OK' if step.success else 'FAIL'}"
            )
            logger.debug(f"  Reason: {step.action.reason}")

        assert result.success, f"Live navigation failed: {result.error}"


class TestLiveIntegrityScenario:
    """Test integrity dashboard with live AI."""

    async def test_live_integrity_view(
        self,
        live_uat_app: JdoApp,
        live_agent: Agent[None, UATAction],
        scenarios_path: Path,
    ) -> None:
        """Live AI can view integrity dashboard."""
        scenario = load_scenario(scenarios_path / "integrity_dashboard.yaml")
        driver = AIUATDriver(live_uat_app, live_agent, debug=True)

        async with live_uat_app.run_test() as pilot:
            result = await driver.run_scenario(scenario, pilot)

        _log_result(result)
        assert result.success, f"Live integrity view failed: {result.error}"


class TestLiveHierarchyScenario:
    """Test hierarchy view with live AI."""

    async def test_live_hierarchy_view(
        self,
        live_uat_app: JdoApp,
        live_agent: Agent[None, UATAction],
        scenarios_path: Path,
    ) -> None:
        """Live AI can view planning hierarchy."""
        scenario = load_scenario(scenarios_path / "planning_hierarchy.yaml")
        driver = AIUATDriver(live_uat_app, live_agent, debug=True)

        async with live_uat_app.run_test() as pilot:
            result = await driver.run_scenario(scenario, pilot)

        _log_result(result)
        assert result.success, f"Live hierarchy view failed: {result.error}"
