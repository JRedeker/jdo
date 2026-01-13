"""Tests for the onboarding module."""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.panel import Panel

from jdo.output.onboarding import (
    APP_VERSION,
    format_onboarding_screen,
    format_whats_new_screen,
    get_last_seen_version,
    set_last_seen_version,
    should_show_onboarding,
    should_show_whats_new,
    show_onboarding_if_needed,
)


class TestFormatOnboardingScreen:
    """Tests for format_onboarding_screen."""

    def test_returns_panel(self) -> None:
        """Returns a Rich Panel."""
        result = format_onboarding_screen()
        assert isinstance(result, Panel)

    def test_panel_has_title(self) -> None:
        """Panel has welcome title."""
        result = format_onboarding_screen()
        assert "Welcome to JDO" in str(result.title)

    def test_panel_has_version_subtitle(self) -> None:
        """Panel subtitle shows version."""
        result = format_onboarding_screen()
        assert APP_VERSION in str(result.subtitle)

    def test_content_mentions_key_commands(self) -> None:
        """Content includes key commands."""
        console = Console(file=StringIO(), force_terminal=True, width=80)
        console.print(format_onboarding_screen())
        output = console.file.getvalue()

        assert "/commit" in output
        assert "/list" in output
        assert "/help" in output


class TestFormatWhatsNewScreen:
    """Tests for format_whats_new_screen."""

    def test_returns_panel(self) -> None:
        """Returns a Rich Panel."""
        result = format_whats_new_screen()
        assert isinstance(result, Panel)

    def test_panel_has_version_in_title(self) -> None:
        """Panel title mentions version."""
        result = format_whats_new_screen()
        assert APP_VERSION in str(result.title)

    def test_content_lists_features(self) -> None:
        """Content lists new features."""
        console = Console(file=StringIO(), force_terminal=True, width=80)
        console.print(format_whats_new_screen())
        output = console.file.getvalue()

        # Should mention key features from v0.1.0
        assert "navigation" in output.lower() or "/view" in output
        assert "keyboard" in output.lower() or "F1" in output


class TestShouldShowOnboarding:
    """Tests for should_show_onboarding."""

    @patch("jdo.output.onboarding.get_last_seen_version")
    def test_returns_true_when_no_version_seen(self, mock_get: MagicMock) -> None:
        """Returns True when last_seen_version is None."""
        mock_get.return_value = None
        assert should_show_onboarding() is True

    @patch("jdo.output.onboarding.get_last_seen_version")
    def test_returns_false_when_version_seen(self, mock_get: MagicMock) -> None:
        """Returns False when user has seen a version."""
        mock_get.return_value = "0.1.0"
        assert should_show_onboarding() is False


class TestShouldShowWhatsNew:
    """Tests for should_show_whats_new."""

    @patch("jdo.output.onboarding.get_last_seen_version")
    def test_returns_false_on_first_run(self, mock_get: MagicMock) -> None:
        """Returns False when last_seen_version is None (first run shows onboarding)."""
        mock_get.return_value = None
        assert should_show_whats_new() is False

    @patch("jdo.output.onboarding.get_last_seen_version")
    def test_returns_false_when_version_matches(self, mock_get: MagicMock) -> None:
        """Returns False when version matches current."""
        mock_get.return_value = APP_VERSION
        assert should_show_whats_new() is False

    @patch("jdo.output.onboarding.get_last_seen_version")
    def test_returns_true_when_version_differs(self, mock_get: MagicMock) -> None:
        """Returns True when version differs from current."""
        mock_get.return_value = "0.0.1"  # Old version
        assert should_show_whats_new() is True


class TestGetLastSeenVersion:
    """Tests for get_last_seen_version."""

    @patch("jdo.output.onboarding._load_user_prefs")
    def test_returns_none_when_no_prefs(self, mock_load: MagicMock) -> None:
        """Returns None when no preferences exist."""
        mock_load.return_value = {}
        assert get_last_seen_version() is None

    @patch("jdo.output.onboarding._load_user_prefs")
    def test_returns_version_from_prefs(self, mock_load: MagicMock) -> None:
        """Returns version from preferences."""
        mock_load.return_value = {"last_seen_version": "1.2.3"}
        assert get_last_seen_version() == "1.2.3"


class TestSetLastSeenVersion:
    """Tests for set_last_seen_version."""

    @patch("jdo.output.onboarding._save_user_prefs")
    @patch("jdo.output.onboarding._load_user_prefs")
    def test_saves_version(self, mock_load: MagicMock, mock_save: MagicMock) -> None:
        """Saves version to preferences."""
        mock_load.return_value = {}
        mock_save.return_value = True

        result = set_last_seen_version("1.0.0")

        assert result is True
        mock_save.assert_called_once()
        saved_prefs = mock_save.call_args[0][0]
        assert saved_prefs["last_seen_version"] == "1.0.0"

    @patch("jdo.output.onboarding._save_user_prefs")
    @patch("jdo.output.onboarding._load_user_prefs")
    def test_preserves_existing_prefs(self, mock_load: MagicMock, mock_save: MagicMock) -> None:
        """Preserves existing preferences when saving."""
        mock_load.return_value = {"other_pref": "value"}
        mock_save.return_value = True

        set_last_seen_version("2.0.0")

        saved_prefs = mock_save.call_args[0][0]
        assert saved_prefs["other_pref"] == "value"
        assert saved_prefs["last_seen_version"] == "2.0.0"


class TestShowOnboardingIfNeeded:
    """Tests for show_onboarding_if_needed."""

    def test_quiet_mode_skips_all(self) -> None:
        """Quiet mode returns False without showing anything."""
        console = Console(file=StringIO(), force_terminal=True)

        result = show_onboarding_if_needed(console, quiet=True)

        assert result is False
        assert console.file.getvalue() == ""

    @patch("jdo.output.onboarding.set_last_seen_version")
    @patch("jdo.output.onboarding.should_show_whats_new")
    @patch("jdo.output.onboarding.should_show_onboarding")
    @patch("builtins.input")
    def test_shows_onboarding_on_first_run(
        self,
        mock_input: MagicMock,
        mock_show_onboarding: MagicMock,
        mock_show_whats_new: MagicMock,
        mock_set_version: MagicMock,
    ) -> None:
        """Shows onboarding screen on first run."""
        mock_show_onboarding.return_value = True
        mock_show_whats_new.return_value = False
        mock_input.return_value = ""

        console = Console(file=StringIO(), force_terminal=True, width=80)
        result = show_onboarding_if_needed(console)

        assert result is True
        assert "Welcome to JDO" in console.file.getvalue()
        mock_set_version.assert_called_once_with(APP_VERSION)

    @patch("jdo.output.onboarding.set_last_seen_version")
    @patch("jdo.output.onboarding.should_show_whats_new")
    @patch("jdo.output.onboarding.should_show_onboarding")
    @patch("builtins.input")
    def test_shows_whats_new_on_version_change(
        self,
        mock_input: MagicMock,
        mock_show_onboarding: MagicMock,
        mock_show_whats_new: MagicMock,
        mock_set_version: MagicMock,
    ) -> None:
        """Shows what's new screen when version changed."""
        mock_show_onboarding.return_value = False
        mock_show_whats_new.return_value = True
        mock_input.return_value = ""

        console = Console(file=StringIO(), force_terminal=True, width=80)
        result = show_onboarding_if_needed(console)

        assert result is True
        assert "What's New" in console.file.getvalue()
        mock_set_version.assert_called_once_with(APP_VERSION)

    @patch("jdo.output.onboarding.should_show_whats_new")
    @patch("jdo.output.onboarding.should_show_onboarding")
    def test_returns_false_when_nothing_to_show(
        self,
        mock_show_onboarding: MagicMock,
        mock_show_whats_new: MagicMock,
    ) -> None:
        """Returns False when nothing to show."""
        mock_show_onboarding.return_value = False
        mock_show_whats_new.return_value = False

        console = Console(file=StringIO(), force_terminal=True)
        result = show_onboarding_if_needed(console)

        assert result is False

    @patch("jdo.output.onboarding.set_last_seen_version")
    @patch("jdo.output.onboarding.should_show_whats_new")
    @patch("jdo.output.onboarding.should_show_onboarding")
    @patch("builtins.input")
    def test_handles_keyboard_interrupt(
        self,
        mock_input: MagicMock,
        mock_show_onboarding: MagicMock,
        mock_show_whats_new: MagicMock,
        mock_set_version: MagicMock,
    ) -> None:
        """Handles KeyboardInterrupt gracefully."""
        mock_show_onboarding.return_value = True
        mock_show_whats_new.return_value = False
        mock_input.side_effect = KeyboardInterrupt()

        console = Console(file=StringIO(), force_terminal=True, width=80)

        # Should not raise
        result = show_onboarding_if_needed(console)

        assert result is True
        mock_set_version.assert_called_once_with(APP_VERSION)

    @patch("jdo.output.onboarding.set_last_seen_version")
    @patch("jdo.output.onboarding.should_show_whats_new")
    @patch("jdo.output.onboarding.should_show_onboarding")
    @patch("builtins.input")
    def test_handles_eof_error(
        self,
        mock_input: MagicMock,
        mock_show_onboarding: MagicMock,
        mock_show_whats_new: MagicMock,
        mock_set_version: MagicMock,
    ) -> None:
        """Handles EOFError gracefully."""
        mock_show_onboarding.return_value = True
        mock_show_whats_new.return_value = False
        mock_input.side_effect = EOFError()

        console = Console(file=StringIO(), force_terminal=True, width=80)

        # Should not raise
        result = show_onboarding_if_needed(console)

        assert result is True
        mock_set_version.assert_called_once_with(APP_VERSION)
