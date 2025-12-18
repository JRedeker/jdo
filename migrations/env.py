"""Alembic migration environment configuration.

This module configures Alembic for SQLModel migrations with SQLite support.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Add the project root to sys.path for model imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import all models to ensure they're registered with SQLModel.metadata
# This is required for autogenerate to detect model changes
from jdo.models import (  # noqa: E402, F401
    CleanupPlan,
    Commitment,
    Draft,
    Goal,
    Milestone,
    RecurringCommitment,
    Stakeholder,
    Task,
    Vision,
)

# Get settings for database path
from jdo.config.settings import get_settings  # noqa: E402

# Alembic Config object for access to .ini file values
config = context.config

# Configure Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = SQLModel.metadata


def get_url() -> str:
    """Get the database URL from settings.

    Returns:
        SQLite database URL.
    """
    settings = get_settings()
    return f"sqlite:///{settings.database_path}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    useful for generating SQL scripts without connecting to a database.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    # Build configuration dictionary
    configuration = {
        "sqlalchemy.url": get_url(),
    }

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite ALTER TABLE support
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
