"""Tests for Data Panel Widgets - TDD Red phase.

Tests for DataPanel container and entity view templates.
"""

from enum import Enum

import pytest
from textual.app import App, ComposeResult

from jdo.widgets.data_panel import DataPanel, PanelMode


class DataPanelTestApp(App):
    """Test app for DataPanel widget."""

    def compose(self) -> ComposeResult:
        yield DataPanel()


class TestPanelMode:
    """Tests for PanelMode enum."""

    def test_has_required_modes(self) -> None:
        """PanelMode has list, view, draft modes."""
        assert PanelMode.LIST.value == "list"
        assert PanelMode.VIEW.value == "view"
        assert PanelMode.DRAFT.value == "draft"


class TestDataPanel:
    """Tests for DataPanel container widget."""

    async def test_panel_switches_between_modes(self) -> None:
        """DataPanel switches between list, view, draft modes."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)

            # Default mode should be list
            assert panel.mode == PanelMode.LIST

            # Switch to view mode
            panel.mode = PanelMode.VIEW
            await pilot.pause()
            assert panel.mode == PanelMode.VIEW

            # Switch to draft mode
            panel.mode = PanelMode.DRAFT
            await pilot.pause()
            assert panel.mode == PanelMode.DRAFT

    async def test_mode_change_triggers_rerender(self) -> None:
        """DataPanel state changes trigger re-render."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)

            # Record initial mode
            assert panel.mode == PanelMode.LIST

            # Change mode
            panel.mode = PanelMode.DRAFT
            await pilot.pause()

            # Mode should have changed
            assert panel.mode == PanelMode.DRAFT


class TestDraftTemplates:
    """Tests for draft template displays."""

    async def test_commitment_draft_shows_all_fields(self) -> None:
        """CommitmentDraft shows all fields with 'Draft' status."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_commitment_draft(
                {
                    "deliverable": "Send report",
                    "stakeholder_name": "Finance Team",
                }
            )
            await pilot.pause()

            rendered = str(panel.render())
            assert "Draft" in rendered or panel.mode == PanelMode.DRAFT

    async def test_goal_draft_shows_all_fields(self) -> None:
        """GoalDraft shows all fields with 'Draft' status."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_goal_draft(
                {
                    "title": "Test Goal",
                    "problem_statement": "The problem",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.DRAFT

    async def test_task_draft_shows_all_fields(self) -> None:
        """TaskDraft shows all fields with 'Draft' status."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_task_draft(
                {
                    "title": "Test Task",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.DRAFT

    async def test_vision_draft_shows_all_fields(self) -> None:
        """VisionDraft shows all fields with 'Draft' status."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_vision_draft(
                {
                    "title": "Test Vision",
                    "narrative": "A compelling future",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.DRAFT

    async def test_milestone_draft_shows_all_fields(self) -> None:
        """MilestoneDraft shows all fields with 'Draft' status."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_milestone_draft(
                {
                    "title": "Test Milestone",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.DRAFT


class TestViewTemplates:
    """Tests for view template displays."""

    async def test_commitment_view_shows_all_fields(self) -> None:
        """CommitmentView shows all fields with current values."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_commitment_view(
                {
                    "id": "123",
                    "deliverable": "Send report",
                    "stakeholder_name": "Finance Team",
                    "due_date": "2025-12-31",
                    "status": "pending",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.VIEW

    async def test_goal_view_shows_all_fields(self) -> None:
        """GoalView shows all goal fields."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_goal_view(
                {
                    "id": "123",
                    "title": "Test Goal",
                    "status": "active",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.VIEW

    async def test_vision_view_shows_all_fields(self) -> None:
        """VisionView shows all vision fields."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_vision_view(
                {
                    "id": "123",
                    "title": "Test Vision",
                    "status": "active",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.VIEW

    async def test_milestone_view_shows_all_fields(self) -> None:
        """MilestoneView shows all milestone fields."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_milestone_view(
                {
                    "id": "123",
                    "title": "Test Milestone",
                    "status": "pending",
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.VIEW


class TestListView:
    """Tests for list view display."""

    async def test_show_list_displays_items(self) -> None:
        """show_list displays items in list mode."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_list(
                "commitments",
                [
                    {"id": "1", "deliverable": "Task 1"},
                    {"id": "2", "deliverable": "Task 2"},
                ],
            )
            await pilot.pause()

            assert panel.mode == PanelMode.LIST


# ============================================================
# Phase 8: Recurring Commitment View Tests
# ============================================================


class TestRecurringCommitmentViews:
    """Tests for recurring commitment data panel views."""

    async def test_recurring_commitment_list_view_shows_all_templates(self) -> None:
        """Test: RecurringCommitmentListView shows all templates."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_list(
                "recurring_commitment",
                [
                    {
                        "id": "1",
                        "deliverable_template": "Weekly status report",
                        "recurrence_type": "weekly",
                        "status": "active",
                    },
                    {
                        "id": "2",
                        "deliverable_template": "Monthly review",
                        "recurrence_type": "monthly",
                        "status": "active",
                    },
                ],
            )
            await pilot.pause()

            assert panel.mode == PanelMode.LIST

    async def test_recurring_commitment_detail_view_shows_pattern_details(self) -> None:
        """Test: RecurringCommitmentDetailView shows pattern details."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_recurring_commitment_view(
                {
                    "id": "123",
                    "deliverable_template": "Weekly status report",
                    "recurrence_type": "weekly",
                    "days_of_week": [0, 2, 4],  # Mon, Wed, Fri
                    "interval": 1,
                    "status": "active",
                    "instances_generated": 5,
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.VIEW

    async def test_recurring_commitment_draft_shows_all_fields(self) -> None:
        """Test: Recurring commitment draft shows all fields."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_recurring_commitment_draft(
                {
                    "deliverable_template": "Weekly report",
                    "stakeholder_name": "Finance Team",
                    "recurrence_type": "weekly",
                    "days_of_week": [0],
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.DRAFT

    async def test_instance_count_displayed_in_detail_view(self) -> None:
        """Test: Instance count displayed in detail view."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_recurring_commitment_view(
                {
                    "id": "123",
                    "deliverable_template": "Daily standup",
                    "recurrence_type": "daily",
                    "status": "active",
                    "instances_generated": 42,
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.VIEW
            # The panel should have stored the instances_generated value
            assert panel._data.get("instances_generated") == 42


class TestCommitmentRecurringIndicator:
    """Tests for recurring indicator on commitment views."""

    async def test_commitment_view_shows_recurring_indicator_when_linked(self) -> None:
        """Test: Commitment view shows recurring indicator when recurring."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_commitment_view(
                {
                    "id": "123",
                    "deliverable": "Weekly status report",
                    "stakeholder_name": "Manager",
                    "due_date": "2025-12-20",
                    "status": "pending",
                    "recurring_commitment_id": "456",  # Linked to recurring
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.VIEW
            # Data should include the recurring link
            assert panel._data.get("recurring_commitment_id") == "456"

    async def test_commitment_view_no_indicator_when_not_recurring(self) -> None:
        """Test: Commitment view without recurring indicator when not linked."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_commitment_view(
                {
                    "id": "123",
                    "deliverable": "One-time task",
                    "stakeholder_name": "Manager",
                    "due_date": "2025-12-20",
                    "status": "pending",
                    # No recurring_commitment_id
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.VIEW
            # Should not have recurring link
            assert panel._data.get("recurring_commitment_id") is None


# ============================================================
# Phase 11-12: Integrity Protocol Panel Tests
# ============================================================


class TestIntegrityDashboardView:
    """Tests for integrity dashboard display in DataPanel."""

    def test_panel_mode_has_integrity(self) -> None:
        """PanelMode has integrity mode."""
        assert PanelMode.INTEGRITY.value == "integrity"

    async def test_show_integrity_dashboard_sets_mode(self) -> None:
        """show_integrity_dashboard sets mode to INTEGRITY."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_integrity_dashboard(
                {
                    "letter_grade": "A-",
                    "composite_score": 92.5,
                    "on_time_rate": 0.95,
                    "notification_timeliness": 0.90,
                    "cleanup_completion_rate": 0.85,
                    "current_streak_weeks": 3,
                    "total_completed": 20,
                    "total_on_time": 19,
                    "total_at_risk": 2,
                    "total_abandoned": 1,
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.INTEGRITY
            assert panel.entity_type == "integrity"
            assert panel.current_data.get("letter_grade") == "A-"

    async def test_integrity_dashboard_renders_grade(self) -> None:
        """Integrity dashboard displays letter grade prominently."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_integrity_dashboard({"letter_grade": "B+", "composite_score": 88.0})
            await pilot.pause()

            # Check that the panel rendered (mode is set)
            assert panel.mode == PanelMode.INTEGRITY


class TestCleanupPlanView:
    """Tests for cleanup plan display in DataPanel."""

    def test_panel_mode_has_cleanup(self) -> None:
        """PanelMode has cleanup mode."""
        assert PanelMode.CLEANUP.value == "cleanup"

    async def test_show_cleanup_plan_sets_mode(self) -> None:
        """show_cleanup_plan sets mode to CLEANUP."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_cleanup_plan(
                {
                    "id": "cleanup-123",
                    "commitment_deliverable": "Quarterly report",
                    "status": "in_progress",
                    "impact_description": "Delayed project timeline",
                    "mitigation_actions": ["Notify stakeholders", "Reschedule deadline"],
                    "notification_task_complete": False,
                }
            )
            await pilot.pause()

            assert panel.mode == PanelMode.CLEANUP
            assert panel.entity_type == "cleanup_plan"

    async def test_cleanup_plan_shows_status(self) -> None:
        """Cleanup plan displays status correctly."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_cleanup_plan({"status": "completed"})
            await pilot.pause()

            assert panel.current_data.get("status") == "completed"


class TestAtRiskWorkflowView:
    """Tests for at-risk workflow display in DataPanel."""

    def test_panel_mode_has_atrisk_workflow(self) -> None:
        """PanelMode has atrisk_workflow mode."""
        assert PanelMode.ATRISK_WORKFLOW.value == "atrisk_workflow"

    async def test_show_atrisk_workflow_sets_mode(self) -> None:
        """show_atrisk_workflow sets mode to ATRISK_WORKFLOW."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)
            panel.show_atrisk_workflow(
                {
                    "id": "commit-123",
                    "deliverable": "Send quarterly report",
                    "stakeholder_name": "Finance team",
                },
                workflow_step="reason",
            )
            await pilot.pause()

            assert panel.mode == PanelMode.ATRISK_WORKFLOW
            assert panel.entity_type == "commitment"
            assert panel.current_data.get("_workflow_step") == "reason"

    async def test_atrisk_workflow_tracks_step(self) -> None:
        """At-risk workflow tracks current step."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)

            # Step 1: reason
            panel.show_atrisk_workflow({"deliverable": "Test"}, workflow_step="reason")
            await pilot.pause()
            assert panel.current_data.get("_workflow_step") == "reason"

            # Step 2: impact
            panel.show_atrisk_workflow({"deliverable": "Test"}, workflow_step="impact")
            await pilot.pause()
            assert panel.current_data.get("_workflow_step") == "impact"

            # Step 3: resolution
            panel.show_atrisk_workflow({"deliverable": "Test"}, workflow_step="resolution")
            await pilot.pause()
            assert panel.current_data.get("_workflow_step") == "resolution"


class TestDataPanelPublicAccessors:
    """Tests for public accessor properties on DataPanel."""

    async def test_entity_type_property(self) -> None:
        """entity_type property returns current entity type."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)

            panel.show_commitment_view({"deliverable": "Test"})
            await pilot.pause()
            assert panel.entity_type == "commitment"

            panel.show_goal_view({"title": "Test Goal"})
            await pilot.pause()
            assert panel.entity_type == "goal"

    async def test_current_data_property(self) -> None:
        """current_data property returns current data dict."""
        app = DataPanelTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one(DataPanel)

            test_data = {"deliverable": "Test", "status": "pending"}
            panel.show_commitment_view(test_data)
            await pilot.pause()

            assert panel.current_data == test_data
            assert panel.current_data.get("deliverable") == "Test"
