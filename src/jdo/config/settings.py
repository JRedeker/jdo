"""Application settings using pydantic-settings."""

from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from jdo.paths import get_database_path


class JDOSettings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables should be prefixed with JDO_.
    Example: JDO_AI_PROVIDER=anthropic
    """

    model_config = SettingsConfigDict(
        env_prefix="JDO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI Provider settings
    ai_provider: str = "anthropic"
    ai_model: str = "claude-sonnet-4-20250514"

    # Database settings
    database_path: Path | None = None

    # Application settings
    timezone: str = "America/New_York"
    log_level: str = "INFO"

    @model_validator(mode="after")
    def set_database_path_default(self) -> Self:
        """Set default database path if not provided."""
        if self.database_path is None:
            self.database_path = get_database_path()
        return self


# Singleton instance storage
_settings_instance: JDOSettings | None = None


def get_settings() -> JDOSettings:
    """Get the application settings singleton.

    Returns:
        The JDOSettings instance.
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = JDOSettings()
    return _settings_instance


def reset_settings() -> None:
    """Reset the settings singleton.

    Useful for testing when you need to reload settings.
    """
    global _settings_instance
    _settings_instance = None
