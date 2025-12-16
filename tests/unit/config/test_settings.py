"""Tests for the settings module - TDD Red phase."""

from pathlib import Path
from unittest.mock import patch

import pytest


class TestJDOSettings:
    """Tests for JDOSettings configuration class."""

    def test_loads_from_env_with_jdo_prefix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JDOSettings loads from environment variables with JDO_ prefix."""
        from jdo.config.settings import JDOSettings

        monkeypatch.setenv("JDO_AI_PROVIDER", "anthropic")
        monkeypatch.setenv("JDO_AI_MODEL", "claude-3-sonnet")

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings()

        assert settings.ai_provider == "anthropic"
        assert settings.ai_model == "claude-3-sonnet"

    def test_ai_provider_env_var_sets_field(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JDO_AI_PROVIDER env var sets ai_provider field."""
        from jdo.config.settings import JDOSettings

        monkeypatch.setenv("JDO_AI_PROVIDER", "openai")

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings()

        assert settings.ai_provider == "openai"

    def test_ai_model_env_var_sets_field(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JDO_AI_MODEL env var sets ai_model field."""
        from jdo.config.settings import JDOSettings

        monkeypatch.setenv("JDO_AI_MODEL", "gpt-4o")

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings()

        assert settings.ai_model == "gpt-4o"

    def test_database_path_env_var_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JDO_DATABASE_PATH env var overrides default database path."""
        from jdo.config.settings import JDOSettings

        custom_db_path = tmp_path / "custom.db"
        monkeypatch.setenv("JDO_DATABASE_PATH", str(custom_db_path))

        settings = JDOSettings()

        assert settings.database_path == custom_db_path

    def test_loads_from_env_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Settings loads from .env file."""
        from jdo.config.settings import JDOSettings

        # Create a .env file in tmp_path
        env_file = tmp_path / ".env"
        env_file.write_text("JDO_AI_PROVIDER=google\nJDO_AI_MODEL=gemini-pro\n")

        # Change to tmp_path so settings picks up the .env file
        monkeypatch.chdir(tmp_path)

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings(_env_file=env_file)

        assert settings.ai_provider == "google"
        assert settings.ai_model == "gemini-pro"

    def test_env_vars_override_env_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env vars override .env file values."""
        from jdo.config.settings import JDOSettings

        # Create a .env file
        env_file = tmp_path / ".env"
        env_file.write_text("JDO_AI_PROVIDER=google\n")

        # But set env var to different value
        monkeypatch.setenv("JDO_AI_PROVIDER", "anthropic")
        monkeypatch.chdir(tmp_path)

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings(_env_file=env_file)

        # Env var should win
        assert settings.ai_provider == "anthropic"

    def test_has_default_values(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Settings has sensible defaults."""
        from jdo.config.settings import JDOSettings

        # Clear any existing env vars
        monkeypatch.delenv("JDO_AI_PROVIDER", raising=False)
        monkeypatch.delenv("JDO_AI_MODEL", raising=False)

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings()

        # Should have default provider and model
        assert settings.ai_provider is not None
        assert settings.ai_model is not None

    def test_timezone_env_var_sets_field(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JDO_TIMEZONE env var sets timezone field."""
        from jdo.config.settings import JDOSettings

        monkeypatch.setenv("JDO_TIMEZONE", "Europe/London")

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings()

        assert settings.timezone == "Europe/London"

    def test_timezone_default_value(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """timezone defaults to America/New_York."""
        from jdo.config.settings import JDOSettings

        monkeypatch.delenv("JDO_TIMEZONE", raising=False)

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings()

        assert settings.timezone == "America/New_York"

    def test_log_level_env_var_sets_field(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JDO_LOG_LEVEL env var sets log_level field."""
        from jdo.config.settings import JDOSettings

        monkeypatch.setenv("JDO_LOG_LEVEL", "DEBUG")

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings()

        assert settings.log_level == "DEBUG"

    def test_log_level_default_value(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """log_level defaults to INFO."""
        from jdo.config.settings import JDOSettings

        monkeypatch.delenv("JDO_LOG_LEVEL", raising=False)

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings()

        assert settings.log_level == "INFO"


class TestSettingsSingleton:
    """Tests for settings singleton pattern."""

    def test_get_settings_returns_same_instance(self, tmp_path: Path) -> None:
        """get_settings returns the same instance."""
        from jdo.config.settings import get_settings, reset_settings

        reset_settings()  # Clear any cached instance

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings1 = get_settings()
            settings2 = get_settings()

        assert settings1 is settings2

    def test_reset_settings_clears_cached_instance(self, tmp_path: Path) -> None:
        """reset_settings clears the cached instance."""
        from jdo.config.settings import get_settings, reset_settings

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings1 = get_settings()
            reset_settings()
            settings2 = get_settings()

        # After reset, should be different instances
        assert settings1 is not settings2

    def test_after_reset_fresh_instance(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """After reset, get_settings returns a fresh instance with new values."""
        from jdo.config.settings import get_settings, reset_settings

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            monkeypatch.setenv("JDO_AI_PROVIDER", "anthropic")
            reset_settings()
            settings1 = get_settings()
            assert settings1.ai_provider == "anthropic"

            monkeypatch.setenv("JDO_AI_PROVIDER", "openai")
            reset_settings()
            settings2 = get_settings()
            assert settings2.ai_provider == "openai"
