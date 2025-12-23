"""Application settings using pydantic-settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Self, get_args

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from jdo.paths import get_database_path, get_log_file_path

# Valid AI providers
AIProvider = Literal["openai", "openrouter"]

# Supported providers tuple (derived from AIProvider for consistency)
SUPPORTED_PROVIDERS: tuple[str, ...] = get_args(AIProvider)


class JDOSettings(BaseSettings):
    """Application settings loaded from environment variables.

    Environment variables should be prefixed with JDO_.
    Example: JDO_AI_PROVIDER=openai
    """

    model_config = SettingsConfigDict(
        env_prefix="JDO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI Provider settings
    ai_provider: AIProvider = "openai"
    ai_model: str = "gpt-5.1-mini"

    # Database settings
    database_path: Path | None = None

    # Logging settings
    log_level: str = "INFO"
    log_file_path: Path | None = None
    log_to_file: bool = False

    # Sentry/Observability settings (optional)
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.1  # 10% of transactions
    environment: str = "development"

    # Application settings
    timezone: str = "America/New_York"

    @model_validator(mode="after")
    def set_defaults(self) -> Self:
        """Set default paths if not provided."""
        if self.database_path is None:
            self.database_path = get_database_path()
        if self.log_file_path is None:
            self.log_file_path = get_log_file_path()
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


def _get_env_file_path() -> Path:
    """Get the path to the .env file.

    Respects JDO_ENV_FILE environment variable override.

    Returns:
        Path to the .env file.
    """
    env_override = os.environ.get("JDO_ENV_FILE")
    if env_override:
        return Path(env_override)
    return Path.cwd() / ".env"


def _load_env_file(path: Path) -> dict[str, str]:
    """Load environment variables from a .env file.

    Parses KEY=VALUE format, skipping comments and blank lines.

    Args:
        path: Path to the .env file.

    Returns:
        Dictionary of environment variable names to values.
    """
    values: dict[str, str] = {}
    if not path.exists():
        return values

    with path.open() as f:
        for raw_line in f:
            stripped = raw_line.strip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                continue
            # Parse KEY=VALUE
            if "=" in stripped:
                key, _, value = stripped.partition("=")
                key = key.strip()
                value = value.strip()
                # Remove surrounding quotes if present (minimum 2 chars for quotes)
                min_quoted_len = 2
                if len(value) >= min_quoted_len and value[0] == value[-1] and value[0] in "\"'":
                    value = value[1:-1]
                values[key] = value
    return values


def _write_env_file(path: Path, values: dict[str, str]) -> None:
    """Write environment variables to a .env file.

    Creates parent directory if needed. Writes atomically via temp file.

    Args:
        path: Path to the .env file.
        values: Dictionary of environment variable names to values.
    """
    # Create parent directory if needed
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build content with sorted keys for deterministic output
    lines: list[str] = []
    for key in sorted(values.keys()):
        value = values[key]
        # Quote values that contain spaces or special chars
        if " " in value or "=" in value or "#" in value:
            value = f'"{value}"'
        lines.append(f"{key}={value}")

    content = "\n".join(lines)
    if lines:
        content += "\n"

    # Write atomically via temp file
    temp_path = path.with_suffix(".env.tmp")
    temp_path.write_text(content)
    temp_path.rename(path)


def set_ai_provider(provider: str) -> AIProvider:
    """Set the AI provider, updating singleton and persisting to .env.

    Args:
        provider: The provider name (openai or openrouter).

    Returns:
        The validated AIProvider value.

    Raises:
        ValueError: If provider is not a supported provider.
    """
    global _settings_instance

    # Validate provider
    if provider not in SUPPORTED_PROVIDERS:
        msg = f"Unsupported provider: {provider}. Must be one of {SUPPORTED_PROVIDERS}"
        raise ValueError(msg)

    # Cast to AIProvider (we validated above)
    validated_provider: AIProvider = provider  # type: ignore[assignment]

    # Update singleton in memory
    current = get_settings()
    # Use model_copy to create updated instance, then replace singleton
    _settings_instance = current.model_copy(update={"ai_provider": validated_provider})

    # Persist to .env file
    env_path = _get_env_file_path()
    env_values = _load_env_file(env_path)
    env_values["JDO_AI_PROVIDER"] = validated_provider
    _write_env_file(env_path, env_values)

    return validated_provider
