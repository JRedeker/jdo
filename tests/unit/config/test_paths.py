"""Tests for the paths module - TDD Red phase."""

from pathlib import Path
from unittest.mock import patch


class TestGetDataDir:
    """Tests for get_data_dir function."""

    def test_returns_platformdirs_user_data_dir(self, tmp_path: Path) -> None:
        """get_data_dir returns platformdirs user_data_dir for 'jdo'."""
        from jdo.paths import get_data_dir

        test_dir = tmp_path / "jdo_data"
        with patch("jdo.paths.user_data_dir") as mock_user_data_dir:
            mock_user_data_dir.return_value = str(test_dir)
            result = get_data_dir()

        mock_user_data_dir.assert_called_once_with("jdo")
        assert result == test_dir

    def test_creates_directory_if_not_exists(self, tmp_path: Path) -> None:
        """get_data_dir creates the directory if it doesn't exist."""
        from jdo.paths import get_data_dir

        test_dir = tmp_path / "jdo_data"
        assert not test_dir.exists()
        with patch("jdo.paths.user_data_dir", return_value=str(test_dir)):
            result = get_data_dir()

        assert result.exists()
        assert result.is_dir()


class TestGetConfigDir:
    """Tests for get_config_dir function."""

    def test_returns_platformdirs_user_config_dir(self, tmp_path: Path) -> None:
        """get_config_dir returns platformdirs user_config_dir for 'jdo'."""
        from jdo.paths import get_config_dir

        test_dir = tmp_path / "jdo_config"
        with patch("jdo.paths.user_config_dir") as mock_user_config_dir:
            mock_user_config_dir.return_value = str(test_dir)
            result = get_config_dir()

        mock_user_config_dir.assert_called_once_with("jdo")
        assert result == test_dir

    def test_creates_directory_if_not_exists(self, tmp_path: Path) -> None:
        """get_config_dir creates the directory if it doesn't exist."""
        from jdo.paths import get_config_dir

        test_dir = tmp_path / "jdo_config"
        assert not test_dir.exists()
        with patch("jdo.paths.user_config_dir", return_value=str(test_dir)):
            result = get_config_dir()

        assert result.exists()
        assert result.is_dir()


class TestGetDatabasePath:
    """Tests for get_database_path function."""

    def test_returns_data_dir_jdo_db(self, tmp_path: Path) -> None:
        """get_database_path returns data_dir / 'jdo.db'."""
        from jdo.paths import get_database_path

        with patch("jdo.paths.get_data_dir", return_value=tmp_path):
            result = get_database_path()

        assert result == tmp_path / "jdo.db"


class TestGetAuthPath:
    """Tests for get_auth_path function."""

    def test_returns_data_dir_auth_json(self, tmp_path: Path) -> None:
        """get_auth_path returns data_dir / 'auth.json'."""
        from jdo.paths import get_auth_path

        with patch("jdo.paths.get_data_dir", return_value=tmp_path):
            result = get_auth_path()

        assert result == tmp_path / "auth.json"
