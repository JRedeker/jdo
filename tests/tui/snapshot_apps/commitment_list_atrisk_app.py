"""Snapshot app for commitment list with at-risk items."""

from __future__ import annotations

from textual.app import App, ComposeResult

from jdo.widgets.data_panel import DataPanel


class CommitmentListAtRiskApp(App):
    """App for testing commitment list with at-risk items."""

    def compose(self) -> ComposeResult:
        yield DataPanel()

    async def on_mount(self) -> None:
        """Mount the app and show commitment list."""
        panel = self.query_one(DataPanel)

        # Show commitment list with mix of statuses including at-risk
        panel.show_list(
            "commitment",
            [
                {
                    "id": "c1",
                    "deliverable": "Complete quarterly financial report",
                    "status": "at_risk",
                    "due_date": "2025-12-20",
                },
                {
                    "id": "c2",
                    "deliverable": "Review and approve vendor contracts",
                    "status": "at_risk",
                    "due_date": "2025-12-22",
                },
                {
                    "id": "c3",
                    "deliverable": "Submit budget proposal",
                    "status": "in_progress",
                    "due_date": "2025-12-25",
                },
                {
                    "id": "c4",
                    "deliverable": "Prepare team performance reviews",
                    "status": "pending",
                    "due_date": "2025-12-30",
                },
                {
                    "id": "c5",
                    "deliverable": "Organize holiday team event",
                    "status": "completed",
                    "due_date": "2025-12-15",
                },
            ],
        )


if __name__ == "__main__":
    CommitmentListAtRiskApp().run()
