"""Onboarding and "What's New" screen formatters.

Displays welcome screens for first-run users and version update notifications.
"""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from jdo.paths import get_config_dir

# Current application version (should match pyproject.toml)
APP_VERSION = "0.1.0"

# Config file for storing user preferences
CONFIG_FILE = "user_prefs.json"


def _get_config_path() -> Path:
    """Get path to user preferences config file."""
    return get_config_dir() / CONFIG_FILE


def _load_user_prefs() -> dict[str, str]:
    """Load user preferences from config file.

    Returns:
        Dictionary of user preferences. Empty dict if file doesn't exist.
    """
    config_path = _get_config_path()
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load user prefs: {}", e)
        return {}


def _save_user_prefs(prefs: dict[str, str]) -> bool:
    """Save user preferences to config file.

    Args:
        prefs: Dictionary of preferences to save.

    Returns:
        True if save succeeded, False otherwise.
    """
    config_path = _get_config_path()
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(prefs, indent=2))
    except OSError as e:
        logger.warning("Failed to save user prefs: {}", e)
        return False
    else:
        return True


def get_last_seen_version() -> str | None:
    """Get the last version the user has seen.

    Returns:
        Version string or None if never seen.
    """
    prefs = _load_user_prefs()
    return prefs.get("last_seen_version")


def set_last_seen_version(version: str) -> bool:
    """Record that user has seen a version.

    Args:
        version: Version string to record.

    Returns:
        True if save succeeded, False otherwise.
    """
    prefs = _load_user_prefs()
    prefs["last_seen_version"] = version
    return _save_user_prefs(prefs)


def should_show_onboarding() -> bool:
    """Check if onboarding should be shown.

    Returns:
        True if this is first run (no last_seen_version).
    """
    return get_last_seen_version() is None


def should_show_whats_new() -> bool:
    """Check if "What's New" should be shown.

    Returns:
        True if version differs from last seen.
    """
    last_seen = get_last_seen_version()
    if last_seen is None:
        return False  # First run shows onboarding, not what's new
    return last_seen != APP_VERSION


def format_onboarding_screen() -> Panel:
    """Format the first-run onboarding screen.

    Returns:
        Rich Panel with welcome message and key commands.
    """
    content = Text()
    content.append("JDO helps you track commitments and maintain accountability.\n\n", style="")
    content.append("Key Commands:\n", style="bold")
    content.append("  /commit ", style="cyan")
    content.append("- Create a new commitment\n", style="")
    content.append("  /list   ", style="cyan")
    content.append("- View your commitments\n", style="")
    content.append("  /help   ", style="cyan")
    content.append("- See all available commands\n", style="")
    content.append("\n")
    content.append("Or just tell me what you need to do in plain English!", style="dim italic")

    return Panel(
        content,
        title="[bold]Welcome to JDO[/bold]",
        subtitle=f"v{APP_VERSION}",
        border_style="blue",
        padding=(1, 2),
    )


def format_whats_new_screen() -> Panel:
    """Format the "What's New" screen for version updates.

    Returns:
        Rich Panel with new features list.
    """
    content = Text()
    content.append("New in this version:\n\n", style="bold")

    # Features for v0.1.0 (initial release)
    features = [
        ("Entity navigation", "Use /view <id> or /1, /2 to quickly view items"),
        ("Keyboard shortcuts", "F1 for help, F5 to refresh, Ctrl+L to clear"),
        ("Fuzzy commands", "Typos get smart suggestions"),
        ("Better help", "Categorized commands with /help"),
    ]

    for name, description in features:
        content.append(f"  • {name}: ", style="cyan")
        content.append(f"{description}\n", style="")

    return Panel(
        content,
        title=f"[bold]What's New in v{APP_VERSION}[/bold]",
        border_style="green",
        padding=(1, 2),
    )


def show_onboarding_if_needed(console: Console, *, quiet: bool = False) -> bool:
    """Show onboarding or what's new screen if needed.

    Args:
        console: Rich console for output.
        quiet: If True, skip all onboarding screens.

    Returns:
        True if a screen was shown, False otherwise.
    """
    if quiet:
        return False

    if should_show_onboarding():
        console.print(format_onboarding_screen())
        console.print("[dim]Press Enter to continue...[/dim]")
        with contextlib.suppress(EOFError, KeyboardInterrupt):
            input()
        set_last_seen_version(APP_VERSION)
        return True

    if should_show_whats_new():
        console.print(format_whats_new_screen())
        console.print("[dim]Press Enter to continue...[/dim]")
        with contextlib.suppress(EOFError, KeyboardInterrupt):
            input()
        set_last_seen_version(APP_VERSION)
        return True

    return False
