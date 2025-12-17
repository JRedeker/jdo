"""Database engine configuration."""

from sqlalchemy import Engine, event
from sqlmodel import create_engine

from jdo.config import get_settings


def _configure_sqlite(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
    """Configure SQLite pragmas for WAL mode and foreign key enforcement."""
    cursor = dbapi_connection.cursor()
    # Enable WAL mode for better concurrent access
    cursor.execute("PRAGMA journal_mode=WAL")
    # Enable foreign key enforcement (required for ON DELETE actions)
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Singleton engine instance
_engine_instance: Engine | None = None


def get_engine() -> Engine:
    """Get the SQLAlchemy/SQLModel database engine.

    Returns a singleton engine instance configured for SQLite.

    Returns:
        The database engine.
    """
    global _engine_instance
    if _engine_instance is None:
        settings = get_settings()
        database_url = f"sqlite:///{settings.database_path}"
        _engine_instance = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
        )
        # Configure SQLite pragmas (WAL mode, foreign keys)
        event.listen(_engine_instance, "connect", _configure_sqlite)
    return _engine_instance


def reset_engine() -> None:
    """Reset the engine singleton.

    Useful for testing when you need a fresh engine.
    """
    global _engine_instance
    if _engine_instance is not None:
        _engine_instance.dispose()
    _engine_instance = None
