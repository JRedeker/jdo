"""Tests for auth public API functions."""

import os

import pytest


class TestGetCredentials:
    """Tests for get_credentials function."""

    def test_get_credentials_returns_stored_credentials(self, tmp_path, monkeypatch):
        """get_credentials returns stored credentials."""
        from jdo.auth.api import get_credentials
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        store = AuthStore(auth_file)
        store.save("openai", ApiKeyCredentials(api_key="sk-stored"))

        creds = get_credentials("openai")
        assert creds is not None
        assert creds.api_key == "sk-stored"

    def test_get_credentials_returns_none_if_not_authenticated(self, tmp_path, monkeypatch):
        """get_credentials returns None if no credentials exist."""
        from jdo.auth.api import get_credentials

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        creds = get_credentials("openai")
        assert creds is None

    def test_get_credentials_checks_env_var_fallback_openai(self, tmp_path, monkeypatch):
        """get_credentials checks OPENAI_API_KEY env var."""
        from jdo.auth.api import get_credentials
        from jdo.auth.models import ApiKeyCredentials

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-env")

        creds = get_credentials("openai")
        assert creds is not None
        assert isinstance(creds, ApiKeyCredentials)
        assert creds.api_key == "sk-openai-env"

    def test_get_credentials_checks_env_var_fallback_openrouter(self, tmp_path, monkeypatch):
        """get_credentials checks OPENROUTER_API_KEY env var."""
        from jdo.auth.api import get_credentials
        from jdo.auth.models import ApiKeyCredentials

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-router-env")

        creds = get_credentials("openrouter")
        assert creds is not None
        assert isinstance(creds, ApiKeyCredentials)
        assert creds.api_key == "sk-router-env"

    def test_get_credentials_stored_takes_precedence_over_env(self, tmp_path, monkeypatch):
        """Stored credentials take precedence over env vars."""
        from jdo.auth.api import get_credentials
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")

        store = AuthStore(auth_file)
        store.save("openai", ApiKeyCredentials(api_key="sk-stored"))

        creds = get_credentials("openai")
        assert creds is not None
        assert creds.api_key == "sk-stored"


class TestGetAuthHeaders:
    """Tests for get_auth_headers function."""

    def test_get_auth_headers_returns_bearer_for_openai(self, tmp_path, monkeypatch):
        """get_auth_headers returns Bearer token for OpenAI."""
        from jdo.auth.api import get_auth_headers
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        store = AuthStore(auth_file)
        store.save("openai", ApiKeyCredentials(api_key="sk-openai-key"))

        headers = get_auth_headers("openai")
        assert headers is not None
        assert headers["Authorization"] == "Bearer sk-openai-key"

    def test_get_auth_headers_returns_bearer_for_openrouter(self, tmp_path, monkeypatch):
        """get_auth_headers returns Bearer token for OpenRouter."""
        from jdo.auth.api import get_auth_headers
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        store = AuthStore(auth_file)
        store.save("openrouter", ApiKeyCredentials(api_key="sk-router-key"))

        headers = get_auth_headers("openrouter")
        assert headers is not None
        assert headers["Authorization"] == "Bearer sk-router-key"

    def test_get_auth_headers_returns_none_if_not_authenticated(self, tmp_path, monkeypatch):
        """get_auth_headers returns None if no credentials."""
        from jdo.auth.api import get_auth_headers

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        headers = get_auth_headers("openai")
        assert headers is None


class TestIsAuthenticated:
    """Tests for is_authenticated function."""

    def test_is_authenticated_returns_true_when_credentials_exist(self, tmp_path, monkeypatch):
        """is_authenticated returns True when credentials exist."""
        from jdo.auth.api import is_authenticated
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        store = AuthStore(auth_file)
        store.save("openai", ApiKeyCredentials(api_key="sk-test"))

        assert is_authenticated("openai") is True

    def test_is_authenticated_returns_false_when_no_credentials(self, tmp_path, monkeypatch):
        """is_authenticated returns False when no credentials."""
        from jdo.auth.api import is_authenticated

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        assert is_authenticated("openai") is False

    def test_is_authenticated_returns_true_for_env_var(self, tmp_path, monkeypatch):
        """is_authenticated returns True when env var is set."""
        from jdo.auth.api import is_authenticated

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")

        assert is_authenticated("openai") is True


class TestClearCredentials:
    """Tests for clear_credentials function."""

    def test_clear_credentials_removes_stored_credentials(self, tmp_path, monkeypatch):
        """clear_credentials removes stored credentials."""
        from jdo.auth.api import clear_credentials, is_authenticated
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        store = AuthStore(auth_file)
        store.save("openai", ApiKeyCredentials(api_key="sk-test"))
        assert is_authenticated("openai") is True

        clear_credentials("openai")
        assert is_authenticated("openai") is False

    def test_clear_credentials_is_idempotent(self, tmp_path, monkeypatch):
        """clear_credentials is idempotent (no error if not exists)."""
        from jdo.auth.api import clear_credentials

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        clear_credentials("nonexistent")


class TestSaveCredentials:
    """Tests for save_credentials function."""

    def test_save_credentials_stores_api_key(self, tmp_path, monkeypatch):
        """save_credentials stores API key credentials."""
        from jdo.auth.api import get_credentials, save_credentials
        from jdo.auth.models import ApiKeyCredentials

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        save_credentials("openai", ApiKeyCredentials(api_key="sk-saved"))

        creds = get_credentials("openai")
        assert creds is not None
        assert creds.api_key == "sk-saved"
