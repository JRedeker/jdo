"""Snapshot app for cleanup plan display."""

from __future__ import annotations

from textual.app import App, ComposeResult

from jdo.widgets.data_panel import DataPanel


class CleanupPlanApp(App):
    """App for testing cleanup plan rendering."""

    def compose(self) -> ComposeResult:
        yield DataPanel()

    async def on_mount(self) -> None:
        """Mount the app and show cleanup plan."""
        panel = self.query_one(DataPanel)

        # Show cleanup plan in progress
        panel.show_cleanup_plan(
            {
                "id": "cleanup-123",
                "commitment_deliverable": "Complete Q4 financial analysis",
                "status": "in_progress",
                "impact_description": (
                    "Board meeting may be delayed by 1 week. "
                    "CFO needs the analysis to prepare budget presentation."
                ),
                "mitigation_actions": [
                    "Notify CFO about 1-week delay",
                    "Provide preliminary findings by original deadline",
                    "Prioritize critical sections: revenue trends and cost analysis",
                    "Request extension for detailed recommendations",
                ],
                "notification_task_complete": True,
            }
        )


if __name__ == "__main__":
    CleanupPlanApp().run()
