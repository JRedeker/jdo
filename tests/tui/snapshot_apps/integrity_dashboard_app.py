"""Snapshot app for integrity dashboard display."""

from __future__ import annotations

from textual.app import App, ComposeResult

from jdo.widgets.data_panel import DataPanel


class IntegrityDashboardApp(App):
    """App for testing integrity dashboard rendering."""

    def compose(self) -> ComposeResult:
        yield DataPanel()

    async def on_mount(self) -> None:
        """Mount the app and show integrity dashboard."""
        panel = self.query_one(DataPanel)

        # Show integrity dashboard with good metrics (A- grade)
        panel.show_integrity_dashboard(
            {
                "letter_grade": "A-",
                "composite_score": 90.5,
                "on_time_rate": 0.95,
                "notification_timeliness": 0.88,
                "cleanup_completion_rate": 0.85,
                "current_streak_weeks": 0,
                "total_completed": 42,
                "total_on_time": 40,
                "total_at_risk": 3,
                "total_abandoned": 1,
            }
        )


if __name__ == "__main__":
    IntegrityDashboardApp().run()
