"""CLI entry point with subcommands for JDO.

Provides both interactive REPL (default) and fire-and-forget CLI commands
like `jdo capture "text"` for quick capture from scripts and shortcuts.
"""

from __future__ import annotations

import click

from jdo.auth.api import is_authenticated, save_credentials
from jdo.auth.models import ApiKeyCredentials
from jdo.db import create_db_and_tables, get_session
from jdo.db.migrations import (
    create_revision,
    downgrade_database,
    get_migration_status,
    upgrade_database,
)
from jdo.models.draft import Draft, EntityType


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """JDO - Just Do One thing at a time.

    Run without arguments to launch the interactive REPL.
    Use subcommands for fire-and-forget operations.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand provided, launch the REPL
        from jdo.repl import run_repl

        run_repl()


@cli.command()
@click.argument("text")
def capture(text: str) -> None:
    """Capture text for later triage.

    Creates a Draft with UNKNOWN entity type that can be
    classified later using the /triage command in the TUI.

    Example:
        jdo capture "Call mom about birthday plans"
        jdo capture "Review quarterly report"
    """
    # Ensure database is initialized
    create_db_and_tables()

    # Create a triage item (Draft with UNKNOWN type)
    draft = Draft(
        entity_type=EntityType.UNKNOWN,
        partial_data={"raw_text": text},
    )

    with get_session() as session:
        session.add(draft)

    click.echo(f"Captured: {text}")


@cli.group()
def db() -> None:
    """Database migration commands."""


@cli.group()
def auth() -> None:
    """Manage AI provider credentials."""


@auth.command("status")
def auth_status() -> None:
    """Show credential status for configured AI providers."""
    providers = ["openai", "openrouter", "anthropic", "google"]
    click.echo("Credential status:")
    for provider in providers:
        if is_authenticated(provider):
            click.echo(f"  ✓ {provider}: configured")
        else:
            click.echo(f"  ✗ {provider}: not configured")
    click.echo("\nTo configure credentials, run: jdo auth set <provider>")


@auth.command("set")
@click.argument("provider", type=click.Choice(["openai", "openrouter", "anthropic", "google"]))
@click.argument("api_key", nargs=-1)
def auth_set(provider: str, api_key: tuple[str, ...]) -> None:
    """Set API key for an AI provider.

    PROVIDER: One of openai, openrouter, anthropic, google

    You can either:
    - Pass the API key as an argument: jdo auth set openai sk-...
    - Enter it interactively when prompted (hidden input)

    Example:
        jdo auth set openai sk-your-api-key
        jdo auth set openrouter sk-or-your-key
    """
    if api_key:
        key = " ".join(api_key)
    else:
        key = click.prompt(
            f"Enter API key for {provider}",
            type=click.STRING,
            hide_input=True,
        )

    if not key:
        click.echo("Error: API key cannot be empty", err=True)
        return

    creds = ApiKeyCredentials(api_key=key)
    save_credentials(provider, creds)
    click.echo(f"✓ {provider} credentials saved successfully")


@db.command("status")
def db_status() -> None:
    """Show current migration status."""
    click.echo("Current migration status:")
    get_migration_status()


@db.command("upgrade")
@click.option("--revision", "-r", default="head", help="Target revision (default: head)")
def db_upgrade(revision: str) -> None:
    """Upgrade database to a later version."""
    click.echo(f"Upgrading database to: {revision}")
    upgrade_database(revision)
    click.echo("Database upgraded successfully.")


@db.command("downgrade")
@click.option("--revision", "-r", default="-1", help="Target revision (default: -1)")
def db_downgrade(revision: str) -> None:
    """Downgrade database to an earlier version."""
    click.echo(f"Downgrading database to: {revision}")
    downgrade_database(revision)
    click.echo("Database downgraded successfully.")


@db.command("revision")
@click.option("--message", "-m", required=True, help="Migration description")
@click.option("--autogenerate/--no-autogenerate", default=True, help="Auto-detect changes")
def db_revision(message: str, *, autogenerate: bool) -> None:
    """Create a new migration revision."""
    click.echo(f"Creating new revision: {message}")
    result = create_revision(message, autogenerate=autogenerate)
    if result:
        click.echo(f"Revision created: {result}")
    else:
        click.echo("No changes detected or revision creation failed.")


def main() -> None:
    """Run the CLI."""
    cli()


if __name__ == "__main__":
    main()
