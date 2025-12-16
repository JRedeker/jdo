"""Database session management."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session

from jdo.db.engine import get_engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session as a context manager.

    Commits on successful exit, rolls back on exception.

    Yields:
        A SQLModel Session.
    """
    engine = get_engine()
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
