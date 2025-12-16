"""Database engine configuration."""

from sqlalchemy import Engine
from sqlmodel import create_engine

from jdo.config import get_settings

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
    return _engine_instance


def reset_engine() -> None:
    """Reset the engine singleton.

    Useful for testing when you need a fresh engine.
    """
    global _engine_instance
    if _engine_instance is not None:
        _engine_instance.dispose()
    _engine_instance = None
