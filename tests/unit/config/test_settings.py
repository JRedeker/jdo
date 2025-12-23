"""Tests for the settings module - TDD Red phase."""

from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError


class TestJDOSettings:
    """Tests for JDOSettings configuration class."""

    def test_loads_from_env_with_jdo_prefix(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JDOSettings loads from environment variables with JDO_ prefix."""
        from jdo.config.settings import JDOSettings

        monkeypatch.setenv("JDO_AI_PROVIDER", "openai")
        monkeypatch.setenv("JDO_AI_MODEL", "gpt-4o")

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings()

        assert settings.ai_provider == "openai"
        assert settings.ai_model == "gpt-4o"

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
        env_file.write_text("JDO_AI_PROVIDER=openai\nJDO_AI_MODEL=gpt-4o\n")

        # Change to tmp_path so settings picks up the .env file
        monkeypatch.chdir(tmp_path)

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings(_env_file=env_file)

        assert settings.ai_provider == "openai"
        assert settings.ai_model == "gpt-4o"

    def test_env_vars_override_env_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env vars override .env file values."""
        from jdo.config.settings import JDOSettings

        # Create a .env file
        env_file = tmp_path / ".env"
        env_file.write_text("JDO_AI_PROVIDER=openrouter\n")

        # But set env var to different value
        monkeypatch.setenv("JDO_AI_PROVIDER", "openai")
        monkeypatch.chdir(tmp_path)

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            settings = JDOSettings(_env_file=env_file)

        # Env var should win
        assert settings.ai_provider == "openai"

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
            monkeypatch.setenv("JDO_AI_PROVIDER", "openai")
            reset_settings()
            settings1 = get_settings()
            assert settings1.ai_provider == "openai"

            monkeypatch.setenv("JDO_AI_PROVIDER", "openrouter")
            reset_settings()
            settings2 = get_settings()
            assert settings2.ai_provider == "openrouter"


class TestEnvFileHelpers:
    """Tests for .env file read/write helpers."""

    def test_load_env_file_parses_key_value(self, tmp_path: Path) -> None:
        """_load_env_file parses KEY=VALUE format correctly."""
        from jdo.config.settings import _load_env_file

        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\nBAZ=qux\n")

        values = _load_env_file(env_file)

        assert values == {"FOO": "bar", "BAZ": "qux"}

    def test_load_env_file_skips_comments(self, tmp_path: Path) -> None:
        """_load_env_file skips comment lines."""
        from jdo.config.settings import _load_env_file

        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nFOO=bar\n# Another comment\nBAZ=qux\n")

        values = _load_env_file(env_file)

        assert values == {"FOO": "bar", "BAZ": "qux"}

    def test_load_env_file_skips_blank_lines(self, tmp_path: Path) -> None:
        """_load_env_file skips blank lines."""
        from jdo.config.settings import _load_env_file

        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\n\nBAZ=qux\n\n")

        values = _load_env_file(env_file)

        assert values == {"FOO": "bar", "BAZ": "qux"}

    def test_load_env_file_handles_quoted_values(self, tmp_path: Path) -> None:
        """_load_env_file removes surrounding quotes from values."""
        from jdo.config.settings import _load_env_file

        env_file = tmp_path / ".env"
        env_file.write_text("FOO=\"bar baz\"\nQUX='single quoted'\n")

        values = _load_env_file(env_file)

        assert values == {"FOO": "bar baz", "QUX": "single quoted"}

    def test_load_env_file_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        """_load_env_file returns empty dict if file doesn't exist."""
        from jdo.config.settings import _load_env_file

        env_file = tmp_path / ".env"  # Does not exist

        values = _load_env_file(env_file)

        assert values == {}

    def test_write_env_file_creates_file(self, tmp_path: Path) -> None:
        """_write_env_file creates the file with KEY=VALUE format."""
        from jdo.config.settings import _write_env_file

        env_file = tmp_path / ".env"
        values = {"FOO": "bar", "BAZ": "qux"}

        _write_env_file(env_file, values)

        content = env_file.read_text()
        assert "FOO=bar" in content
        assert "BAZ=qux" in content

    def test_write_env_file_creates_parent_directory(self, tmp_path: Path) -> None:
        """_write_env_file creates parent directory if needed."""
        from jdo.config.settings import _write_env_file

        env_file = tmp_path / "subdir" / ".env"
        values = {"FOO": "bar"}

        _write_env_file(env_file, values)

        assert env_file.exists()
        assert "FOO=bar" in env_file.read_text()

    def test_write_env_file_quotes_values_with_spaces(self, tmp_path: Path) -> None:
        """_write_env_file quotes values containing spaces."""
        from jdo.config.settings import _write_env_file

        env_file = tmp_path / ".env"
        values = {"FOO": "bar baz"}

        _write_env_file(env_file, values)

        content = env_file.read_text()
        assert 'FOO="bar baz"' in content

    def test_write_env_file_sorts_keys(self, tmp_path: Path) -> None:
        """_write_env_file sorts keys alphabetically."""
        from jdo.config.settings import _write_env_file

        env_file = tmp_path / ".env"
        values = {"ZZZ": "last", "AAA": "first", "MMM": "middle"}

        _write_env_file(env_file, values)

        content = env_file.read_text()
        lines = content.strip().split("\n")
        keys = [line.split("=")[0] for line in lines]
        assert keys == ["AAA", "MMM", "ZZZ"]


class TestSetAiProvider:
    """Tests for set_ai_provider function."""

    def test_updates_singleton_instance(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """set_ai_provider updates the singleton in memory."""
        from jdo.config.settings import get_settings, reset_settings, set_ai_provider

        # Use tmp_path for env file to avoid polluting real .env
        monkeypatch.setenv("JDO_ENV_FILE", str(tmp_path / ".env"))
        # Ensure no env var pollutes the default
        monkeypatch.delenv("JDO_AI_PROVIDER", raising=False)
        # Change to tmp_path to avoid loading the project .env file
        monkeypatch.chdir(tmp_path)

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            reset_settings()
            settings = get_settings()
            assert settings.ai_provider == "openai"  # Default

            set_ai_provider("openrouter")

            settings = get_settings()
            assert settings.ai_provider == "openrouter"

    def test_writes_to_env_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """set_ai_provider persists the choice to .env file."""
        from jdo.config.settings import reset_settings, set_ai_provider

        env_file = tmp_path / ".env"
        monkeypatch.setenv("JDO_ENV_FILE", str(env_file))

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            reset_settings()
            set_ai_provider("openrouter")

        content = env_file.read_text()
        assert "JDO_AI_PROVIDER=openrouter" in content

    def test_preserves_other_env_values(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """set_ai_provider preserves existing .env values."""
        from jdo.config.settings import reset_settings, set_ai_provider

        env_file = tmp_path / ".env"
        env_file.write_text("JDO_AI_MODEL=gpt-4o\nOTHER_VAR=value\n")
        monkeypatch.setenv("JDO_ENV_FILE", str(env_file))

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            reset_settings()
            set_ai_provider("openrouter")

        content = env_file.read_text()
        assert "JDO_AI_PROVIDER=openrouter" in content
        assert "JDO_AI_MODEL=gpt-4o" in content
        assert "OTHER_VAR=value" in content

    def test_raises_for_invalid_provider(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """set_ai_provider raises ValueError for unsupported provider."""
        from jdo.config.settings import reset_settings, set_ai_provider

        monkeypatch.setenv("JDO_ENV_FILE", str(tmp_path / ".env"))

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            reset_settings()
            with pytest.raises(ValueError, match="Unsupported provider"):
                set_ai_provider("invalid_provider")

    def test_returns_validated_provider(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """set_ai_provider returns the validated AIProvider value."""
        from jdo.config.settings import reset_settings, set_ai_provider

        monkeypatch.setenv("JDO_ENV_FILE", str(tmp_path / ".env"))

        with patch("jdo.config.settings.get_database_path", return_value=tmp_path / "test.db"):
            reset_settings()
            result = set_ai_provider("openrouter")

        assert result == "openrouter"
