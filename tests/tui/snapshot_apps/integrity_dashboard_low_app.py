"""Snapshot app for low integrity score dashboard."""

from __future__ import annotations

from textual.app import App, ComposeResult

from jdo.widgets.data_panel import DataPanel


class IntegrityDashboardLowApp(App):
    """App for testing low integrity score rendering."""

    def compose(self) -> ComposeResult:
        yield DataPanel()

    async def on_mount(self) -> None:
        """Mount the app and show low integrity dashboard."""
        panel = self.query_one(DataPanel)

        # Show integrity dashboard with poor metrics (C- grade)
        panel.show_integrity_dashboard(
            {
                "letter_grade": "C-",
                "composite_score": 70.2,
                "on_time_rate": 0.65,
                "notification_timeliness": 0.45,
                "cleanup_completion_rate": 0.50,
                "current_streak_weeks": 0,
                "total_completed": 20,
                "total_on_time": 13,
                "total_at_risk": 8,
                "total_abandoned": 4,
            }
        )


if __name__ == "__main__":
    IntegrityDashboardLowApp().run()
