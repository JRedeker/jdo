"""Database schema management and migrations.

This module provides database table creation and migration management
using Alembic for versioned schema changes.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlmodel import SQLModel

from jdo.db.engine import get_engine

# Import all models to ensure they're registered with SQLModel.metadata
from jdo.models import Commitment, Goal, Stakeholder, Task  # noqa: F401


def get_alembic_config() -> Config:
    """Get Alembic configuration for the project.

    Returns:
        Alembic Config object pointing to migrations directory.
    """
    # Find the migrations directory relative to this file
    migrations_dir = Path(__file__).parent.parent.parent.parent / "migrations"
    config_path = migrations_dir / "alembic.ini"

    cfg = Config(str(config_path))
    cfg.set_main_option("script_location", str(migrations_dir))

    return cfg


def create_db_and_tables() -> None:
    """Create all database tables.

    Creates all tables defined by SQLModel table classes.
    Safe to call multiple times - existing tables are preserved.
    """
    engine = get_engine()
    SQLModel.metadata.create_all(engine)


def get_migration_status() -> None:
    """Display current migration status.

    Prints current migration head and pending migrations to stdout.
    """
    cfg = get_alembic_config()
    command.current(cfg, verbose=True)


def upgrade_database(revision: str = "head") -> None:
    """Upgrade database to a later version.

    Args:
        revision: Target revision (default "head" for latest).
    """
    cfg = get_alembic_config()
    command.upgrade(cfg, revision)


def downgrade_database(revision: str = "-1") -> None:
    """Downgrade database to an earlier version.

    Args:
        revision: Target revision (default "-1" for one step back).
    """
    cfg = get_alembic_config()
    command.downgrade(cfg, revision)


def create_revision(message: str, *, autogenerate: bool = True) -> None:
    """Create a new migration revision.

    Args:
        message: Description of the migration.
        autogenerate: Whether to auto-detect model changes.
    """
    cfg = get_alembic_config()
    command.revision(cfg, message=message, autogenerate=autogenerate)
