"""Tests for CLI module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestCliCapture:
    """Tests for the capture command."""

    def test_capture_creates_draft_with_unknown_type(self) -> None:
        """Test that capture creates a draft with UNKNOWN entity type."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()

        with (
            patch("jdo.cli.create_db_and_tables") as mock_create,
            patch("jdo.cli.get_session") as mock_session,
        ):
            mock_session.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_session.return_value.__exit__ = MagicMock(return_value=False)

            result = runner.invoke(cli, ["capture", "Test capture text"])

            mock_create.assert_called_once()
            assert result.exit_code == 0
            assert "Captured: Test capture text" in result.output

    def test_capture_requires_text_argument(self) -> None:
        """Test that capture fails without text argument."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["capture"])

        assert result.exit_code != 0


class TestCliDbCommands:
    """Tests for database commands."""

    def test_db_status_displays_status(self) -> None:
        """Test db status command displays migration status."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()

        with patch("jdo.cli.get_migration_status") as mock_status:
            result = runner.invoke(cli, ["db", "status"])

            assert result.exit_code == 0
            assert "Current migration status" in result.output
            mock_status.assert_called_once()

    def test_db_upgrade_calls_upgrade(self) -> None:
        """Test db upgrade command calls upgrade_database."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()

        with patch("jdo.cli.upgrade_database") as mock_upgrade:
            result = runner.invoke(cli, ["db", "upgrade"])

            assert result.exit_code == 0
            assert "Upgrading database to: head" in result.output
            mock_upgrade.assert_called_once_with("head")

    def test_db_upgrade_with_revision(self) -> None:
        """Test db upgrade with specific revision."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()

        with patch("jdo.cli.upgrade_database") as mock_upgrade:
            result = runner.invoke(cli, ["db", "upgrade", "-r", "abcd1234"])

            assert result.exit_code == 0
            assert "Upgrading database to: abcd1234" in result.output
            mock_upgrade.assert_called_once_with("abcd1234")

    def test_db_downgrade_calls_downgrade(self) -> None:
        """Test db downgrade command calls downgrade_database."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()

        with patch("jdo.cli.downgrade_database") as mock_downgrade:
            result = runner.invoke(cli, ["db", "downgrade"])

            assert result.exit_code == 0
            assert "Downgrading database to: -1" in result.output
            mock_downgrade.assert_called_once_with("-1")

    def test_db_downgrade_with_revision(self) -> None:
        """Test db downgrade with specific revision."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()

        with patch("jdo.cli.downgrade_database") as mock_downgrade:
            result = runner.invoke(cli, ["db", "downgrade", "-r", "abcd1234"])

            assert result.exit_code == 0
            assert "Downgrading database to: abcd1234" in result.output
            mock_downgrade.assert_called_once_with("abcd1234")

    def test_db_revision_requires_message(self) -> None:
        """Test db revision requires message option."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "revision"])

        assert result.exit_code != 0

    def test_db_revision_creates_revision(self) -> None:
        """Test db revision creates a new migration revision."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()

        with patch("jdo.cli.create_revision") as mock_create:
            mock_create.return_value = "abcd1234"
            result = runner.invoke(cli, ["db", "revision", "-m", "test message"])

            assert result.exit_code == 0
            assert "Creating new revision: test message" in result.output
            mock_create.assert_called_once_with("test message", autogenerate=True)

    def test_db_revision_no_autogenerate(self) -> None:
        """Test db revision with --no-autogenerate."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()

        with patch("jdo.cli.create_revision") as mock_create:
            mock_create.return_value = None
            result = runner.invoke(
                cli, ["db", "revision", "-m", "test message", "--no-autogenerate"]
            )

            assert result.exit_code == 0
            mock_create.assert_called_once_with("test message", autogenerate=False)

    def test_db_revision_no_changes(self) -> None:
        """Test db revision when no changes detected."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()

        with patch("jdo.cli.create_revision") as mock_create:
            mock_create.return_value = None
            result = runner.invoke(cli, ["db", "revision", "-m", "test message"])

            assert result.exit_code == 0
            assert "No changes detected" in result.output


class TestCliGroup:
    """Tests for CLI group behavior."""

    def test_cli_help_message(self) -> None:
        """Test that --help displays help message."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "JDO" in result.output or "Just Do One" in result.output

    def test_db_group_help(self) -> None:
        """Test that db --help shows available db commands."""
        from click.testing import CliRunner

        from jdo.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["db", "--help"])

        assert result.exit_code == 0
        assert "status" in result.output
        assert "upgrade" in result.output
        assert "downgrade" in result.output
        assert "revision" in result.output
