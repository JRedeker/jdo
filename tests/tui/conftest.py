"""TUI test fixtures for JDO."""

import pytest


@pytest.fixture
def app():
    """Create a JDOApp instance for testing.

    Note: This fixture will be implemented when the TUI app exists.
    For now, it returns None as a placeholder.
    """
    # TODO: Import and return JDOApp when add-conversational-tui is implemented
    # from jdo.app import JDOApp
    # return JDOApp()
    pytest.skip("JDOApp not yet implemented")


@pytest.fixture
async def pilot(app):
    """Create a Pilot instance for TUI testing.

    Yields a Pilot from app.run_test() for simulating user interactions.

    Note: This fixture will be implemented when the TUI app exists.
    """
    # TODO: Implement when add-conversational-tui is complete
    # async with app.run_test() as pilot:
    #     yield pilot
    pytest.skip("JDOApp not yet implemented")
