"""Snapshot tests for visual regression testing.

Phase 16: Visual Regression - captures screenshots of key UI states.

Run with: pytest tests/tui/test_snapshots.py -v
Update snapshots with: pytest tests/tui/test_snapshots.py --snapshot-update
"""

import pytest


class TestHomeScreenSnapshots:
    """Snapshot tests for HomeScreen."""

    def test_home_screen_empty_state(self, snap_compare: object) -> None:
        """Snapshot of HomeScreen in empty state."""
        from pathlib import Path

        app_path = Path(__file__).parent / "snapshot_apps" / "home_screen_app.py"
        assert snap_compare(  # type: ignore[operator]
            str(app_path),
            terminal_size=(80, 24),
        )

    def test_home_screen_ai_required_modal(self, snap_compare: object) -> None:
        """Snapshot of AI-required modal."""
        from pathlib import Path

        app_path = Path(__file__).parent / "snapshot_apps" / "home_screen_ai_required_app.py"
        assert snap_compare(  # type: ignore[operator]
            str(app_path),
            terminal_size=(80, 24),
        )


class TestDataPanelSnapshots:
    """Snapshot tests for DataPanel widget."""

    @pytest.fixture
    def data_panel_draft_app(self, tmp_path: object) -> str:
        """Create a temporary app file for DataPanel draft mode."""
        # Create app dynamically
        app_code = """
from textual.app import App, ComposeResult
from jdo.widgets.data_panel import DataPanel

class DataPanelDraftApp(App):
    def compose(self) -> ComposeResult:
        yield DataPanel()

    def on_mount(self) -> None:
        panel = self.query_one(DataPanel)
        panel.show_commitment_draft({
            "deliverable": "Send quarterly report",
            "stakeholder_name": "Finance Team",
            "due_date": "2025-12-20",
        })

if __name__ == "__main__":
    DataPanelDraftApp().run()
"""
        from pathlib import Path

        app_file = Path(str(tmp_path)) / "data_panel_draft_app.py"
        app_file.write_text(app_code)
        return str(app_file)

    @pytest.fixture
    def data_panel_list_app(self, tmp_path: object) -> str:
        """Create a temporary app file for DataPanel list mode."""
        app_code = """
from textual.app import App, ComposeResult
from jdo.widgets.data_panel import DataPanel

class DataPanelListApp(App):
    def compose(self) -> ComposeResult:
        yield DataPanel()

    def on_mount(self) -> None:
        panel = self.query_one(DataPanel)
        panel.show_list("commitment", [
            {"id": "1", "deliverable": "Task 1"},
            {"id": "2", "deliverable": "Task 2"},
            {"id": "3", "deliverable": "Task 3"},
        ])

if __name__ == "__main__":
    DataPanelListApp().run()
"""
        from pathlib import Path

        app_file = Path(str(tmp_path)) / "data_panel_list_app.py"
        app_file.write_text(app_code)
        return str(app_file)

    @pytest.fixture
    def data_panel_empty_app(self, tmp_path: object) -> str:
        """Create a temporary app file for DataPanel empty state."""
        app_code = """
from textual.app import App, ComposeResult
from jdo.widgets.data_panel import DataPanel

class DataPanelEmptyApp(App):
    def compose(self) -> ComposeResult:
        yield DataPanel()

    def on_mount(self) -> None:
        panel = self.query_one(DataPanel)
        panel.show_list("commitment", [])

if __name__ == "__main__":
    DataPanelEmptyApp().run()
"""
        from pathlib import Path

        app_file = Path(str(tmp_path)) / "data_panel_empty_app.py"
        app_file.write_text(app_code)
        return str(app_file)

    def test_data_panel_draft_mode(self, snap_compare: object, data_panel_draft_app: str) -> None:
        """Snapshot of DataPanel in draft mode."""
        assert snap_compare(  # type: ignore[operator]
            data_panel_draft_app,
            terminal_size=(60, 20),
        )

    def test_data_panel_list_mode(self, snap_compare: object, data_panel_list_app: str) -> None:
        """Snapshot of DataPanel in list mode."""
        assert snap_compare(  # type: ignore[operator]
            data_panel_list_app,
            terminal_size=(60, 20),
        )

    def test_data_panel_empty_list(self, snap_compare: object, data_panel_empty_app: str) -> None:
        """Snapshot of DataPanel with empty list and guidance."""
        assert snap_compare(  # type: ignore[operator]
            data_panel_empty_app,
            terminal_size=(60, 20),
        )


class TestHierarchyViewSnapshots:
    """Snapshot tests for HierarchyView widget."""

    @pytest.fixture
    def hierarchy_view_app(self, tmp_path: object) -> str:
        """Create a temporary app file for HierarchyView."""
        app_code = """
from textual.app import App, ComposeResult
from jdo.widgets.hierarchy_view import HierarchyView

class HierarchyViewApp(App):
    def compose(self) -> ComposeResult:
        yield HierarchyView()

    def on_mount(self) -> None:
        view = self.query_one(HierarchyView)
        v1 = view.add_vision("v1", "Become market leader")
        g1 = view.add_goal("g1", "Increase sales 50%", parent_node=v1)
        m1 = view.add_milestone("m1", "Q1 target: 25%", parent_node=g1)
        view.add_commitment("c1", "Close deal with Acme", parent_node=m1)
        view.add_commitment("c2", "Launch campaign", parent_node=m1)
        view.add_orphan_commitment("c3", "Follow up emails")

if __name__ == "__main__":
    HierarchyViewApp().run()
"""
        from pathlib import Path

        app_file = Path(str(tmp_path)) / "hierarchy_view_app.py"
        app_file.write_text(app_code)
        return str(app_file)

    def test_hierarchy_view_tree(self, snap_compare: object, hierarchy_view_app: str) -> None:
        """Snapshot of HierarchyView with tree structure."""
        assert snap_compare(  # type: ignore[operator]
            hierarchy_view_app,
            terminal_size=(80, 24),
        )


class TestChatScreenSnapshots:
    """Snapshot tests for ChatScreen."""

    @pytest.fixture
    def chat_screen_app(self, tmp_path: object) -> str:
        """Create a temporary app file for ChatScreen."""
        app_code = """
from textual.app import App, ComposeResult
from jdo.screens.chat import ChatScreen

class ChatScreenApp(App):
    def compose(self) -> ComposeResult:
        yield ChatScreen()

if __name__ == "__main__":
    ChatScreenApp().run()
"""
        from pathlib import Path

        app_file = Path(str(tmp_path)) / "chat_screen_app.py"
        app_file.write_text(app_code)
        return str(app_file)

    def test_chat_screen_empty(self, snap_compare: object, chat_screen_app: str) -> None:
        """Snapshot of ChatScreen in initial state."""
        assert snap_compare(  # type: ignore[operator]
            chat_screen_app,
            terminal_size=(100, 30),
        )


class TestIntegritySnapshots:
    """Snapshot tests for integrity protocol features."""

    def test_integrity_dashboard_good_grade(self, snap_compare: object) -> None:
        """Snapshot of integrity dashboard with A- grade."""
        from pathlib import Path

        app_path = Path(__file__).parent / "snapshot_apps" / "integrity_dashboard_app.py"
        assert snap_compare(  # type: ignore[operator]
            str(app_path),
            terminal_size=(60, 30),
        )

    def test_integrity_dashboard_low_grade(self, snap_compare: object) -> None:
        """Snapshot of integrity dashboard with C- grade."""
        from pathlib import Path

        app_path = Path(__file__).parent / "snapshot_apps" / "integrity_dashboard_low_app.py"
        assert snap_compare(  # type: ignore[operator]
            str(app_path),
            terminal_size=(60, 30),
        )

    def test_cleanup_plan_display(self, snap_compare: object) -> None:
        """Snapshot of cleanup plan in data panel."""
        from pathlib import Path

        app_path = Path(__file__).parent / "snapshot_apps" / "cleanup_plan_app.py"
        assert snap_compare(  # type: ignore[operator]
            str(app_path),
            terminal_size=(60, 30),
        )

    def test_commitment_list_with_atrisk(self, snap_compare: object) -> None:
        """Snapshot of commitment list with at-risk items."""
        from pathlib import Path

        app_path = Path(__file__).parent / "snapshot_apps" / "commitment_list_atrisk_app.py"
        assert snap_compare(  # type: ignore[operator]
            str(app_path),
            terminal_size=(60, 25),
        )
