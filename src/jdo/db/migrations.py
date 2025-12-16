"""Database schema management."""

from sqlmodel import SQLModel

from jdo.db.engine import get_engine

# Import all models to ensure they're registered with SQLModel.metadata
from jdo.models import Commitment, Goal, Stakeholder, Task  # noqa: F401


def create_db_and_tables() -> None:
    """Create all database tables.

    Creates all tables defined by SQLModel table classes.
    Safe to call multiple times - existing tables are preserved.
    """
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
