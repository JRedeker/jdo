"""Tests for the vision formatters module."""

from unittest.mock import MagicMock
from uuid import uuid4

from rich.panel import Panel
from rich.table import Table

from jdo.models.vision import VisionStatus
from jdo.output.vision import (
    VISION_STATUS_COLORS,
    format_vision_detail,
    format_vision_list,
    format_vision_list_plain,
    format_vision_proposal,
    get_vision_status_color,
)


class TestGetVisionStatusColor:
    """Tests for vision status color mapping."""

    def test_active_status(self):
        """Active status returns green."""
        assert get_vision_status_color("active") == "green"
        assert get_vision_status_color(VisionStatus.ACTIVE) == "green"

    def test_achieved_status(self):
        """Achieved status returns cyan."""
        assert get_vision_status_color("achieved") == "cyan"
        assert get_vision_status_color(VisionStatus.ACHIEVED) == "cyan"

    def test_evolved_status(self):
        """Evolved status returns blue."""
        assert get_vision_status_color("evolved") == "blue"
        assert get_vision_status_color(VisionStatus.EVOLVED) == "blue"

    def test_abandoned_status(self):
        """Abandoned status returns red."""
        assert get_vision_status_color("abandoned") == "red"
        assert get_vision_status_color(VisionStatus.ABANDONED) == "red"

    def test_unknown_status(self):
        """Unknown status returns default."""
        assert get_vision_status_color("unknown") == "default"


class TestFormatVisionList:
    """Tests for vision list formatting."""

    def test_empty_list_returns_table(self):
        """Empty list returns empty table."""
        table = format_vision_list([])
        assert isinstance(table, Table)

    def test_table_has_expected_columns(self):
        """Table has expected columns."""
        table = format_vision_list([])
        column_names = [col.header for col in table.columns]
        assert "ID" in column_names
        assert "Title" in column_names
        assert "Timeframe" in column_names
        assert "Status" in column_names
        assert "Review Due" in column_names


class TestFormatVisionDetail:
    """Tests for vision detail formatting."""

    def test_returns_panel(self):
        """Detail view returns a Panel."""
        vision = MagicMock()
        vision.id = uuid4()
        vision.title = "Test Vision"
        vision.narrative = "A vision of the future"
        vision.timeframe = "5 years"
        vision.status = VisionStatus.ACTIVE
        vision.why_it_matters = None
        vision.metrics = []
        vision.next_review_date = None

        panel = format_vision_detail(vision)
        assert isinstance(panel, Panel)


class TestFormatVisionProposal:
    """Tests for vision proposal formatting."""

    def test_returns_panel(self):
        """Proposal returns a Panel."""
        panel = format_vision_proposal(
            title="My Vision",
            narrative="A vivid future",
            timeframe="5 years",
        )
        assert isinstance(panel, Panel)

    def test_contains_title(self):
        """Panel contains title text."""
        panel = format_vision_proposal(
            title="Published Author",
            narrative="I see myself with 3 bestselling books",
            timeframe="5 years",
        )
        content = str(panel.renderable)
        assert "Published Author" in content

    def test_contains_metrics_when_provided(self):
        """Panel contains metrics when provided."""
        panel = format_vision_proposal(
            title="My Vision",
            narrative="The future",
            metrics=["3 books published", "1000 readers"],
        )
        content = str(panel.renderable)
        assert "3 books published" in content

    def test_contains_confirmation_prompt(self):
        """Panel contains confirmation prompt."""
        panel = format_vision_proposal(
            title="My Vision",
            narrative="The future",
        )
        content = str(panel.renderable)
        assert "Does this look right?" in content


class TestFormatVisionListPlain:
    """Tests for plain text vision list formatting."""

    def test_empty_list(self):
        """Empty list returns friendly message."""
        result = format_vision_list_plain([])
        assert "No vision" in result

    def test_single_vision(self):
        """Single vision is formatted correctly."""
        visions = [
            {
                "id": "1",
                "title": "Published Author",
                "timeframe": "5 years",
                "status": "active",
            }
        ]
        result = format_vision_list_plain(visions)
        assert "Published Author" in result
        assert "5 years" in result


class TestVisionStatusColors:
    """Tests for VISION_STATUS_COLORS constant."""

    def test_all_statuses_have_colors(self):
        """All vision statuses have colors defined."""
        for status in VisionStatus:
            assert status.value in VISION_STATUS_COLORS
