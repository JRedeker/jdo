"""Application path management using platformdirs."""

from pathlib import Path

from platformdirs import user_config_dir, user_data_dir


def get_data_dir() -> Path:
    """Get the user data directory for jdo.

    Creates the directory if it doesn't exist.

    Returns:
        Path to the data directory.
    """
    path = Path(user_data_dir("jdo"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_dir() -> Path:
    """Get the user config directory for jdo.

    Creates the directory if it doesn't exist.

    Returns:
        Path to the config directory.
    """
    path = Path(user_config_dir("jdo"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_database_path() -> Path:
    """Get the path to the SQLite database file.

    Returns:
        Path to jdo.db in the data directory.
    """
    return get_data_dir() / "jdo.db"


def get_auth_path() -> Path:
    """Get the path to the auth credentials file.

    Returns:
        Path to auth.json in the data directory.
    """
    return get_data_dir() / "auth.json"
