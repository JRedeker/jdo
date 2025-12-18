"""CLI entry point with subcommands for JDO.

Provides both interactive TUI (default) and fire-and-forget CLI commands
like `jdo capture "text"` for quick capture from scripts and shortcuts.
"""

import click

from jdo.db import create_db_and_tables, get_session
from jdo.models.draft import Draft, EntityType


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """JDO - Just Do One thing at a time.

    Run without arguments to launch the interactive TUI.
    Use subcommands for fire-and-forget operations.
    """
    if ctx.invoked_subcommand is None:
        # No subcommand provided, launch the TUI
        from jdo.app import main

        main()


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


def main() -> None:
    """Run the CLI."""
    cli()


if __name__ == "__main__":
    main()
