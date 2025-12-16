"""Tests for auth public API functions."""

import os
import time

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

        # Store credentials directly
        store = AuthStore(auth_file)
        store.save("openai", ApiKeyCredentials(api_key="sk-stored"))

        # Get should return them
        creds = get_credentials("openai")
        assert creds is not None
        assert creds.api_key == "sk-stored"

    def test_get_credentials_returns_none_if_not_authenticated(self, tmp_path, monkeypatch):
        """get_credentials returns None if no credentials exist."""
        from jdo.auth.api import get_credentials

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        # Clear any env vars
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        creds = get_credentials("openai")
        assert creds is None

    def test_get_credentials_checks_env_var_fallback_anthropic(self, tmp_path, monkeypatch):
        """get_credentials checks ANTHROPIC_API_KEY env var."""
        from jdo.auth.api import get_credentials
        from jdo.auth.models import ApiKeyCredentials

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")

        creds = get_credentials("anthropic")
        assert creds is not None
        assert isinstance(creds, ApiKeyCredentials)
        assert creds.api_key == "sk-from-env"

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

        # Store credentials
        store = AuthStore(auth_file)
        store.save("openai", ApiKeyCredentials(api_key="sk-stored"))

        creds = get_credentials("openai")
        assert creds is not None
        assert creds.api_key == "sk-stored"


class TestGetAuthHeaders:
    """Tests for get_auth_headers function."""

    def test_get_auth_headers_returns_bearer_for_oauth(self, tmp_path, monkeypatch):
        """get_auth_headers returns Bearer token for OAuth credentials."""
        from jdo.auth.api import get_auth_headers
        from jdo.auth.models import OAuthCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        expires = int(time.time() * 1000) + 3600000
        store = AuthStore(auth_file)
        store.save(
            "anthropic",
            OAuthCredentials(
                access_token="oauth_token_xyz",
                refresh_token="refresh_abc",
                expires_at=expires,
            ),
        )

        headers = get_auth_headers("anthropic")
        assert headers is not None
        assert headers["Authorization"] == "Bearer oauth_token_xyz"
        assert "anthropic-beta" in headers

    def test_get_auth_headers_includes_anthropic_beta_for_oauth(self, tmp_path, monkeypatch):
        """OAuth headers include anthropic-beta header."""
        from jdo.auth.api import get_auth_headers
        from jdo.auth.models import OAuthCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        expires = int(time.time() * 1000) + 3600000
        store = AuthStore(auth_file)
        store.save(
            "anthropic",
            OAuthCredentials(
                access_token="oauth_token",
                refresh_token="refresh",
                expires_at=expires,
            ),
        )

        headers = get_auth_headers("anthropic")
        assert headers["anthropic-beta"] == "oauth-2025-04-20"

    def test_get_auth_headers_returns_x_api_key_for_anthropic_api(self, tmp_path, monkeypatch):
        """get_auth_headers returns x-api-key for Anthropic API key."""
        from jdo.auth.api import get_auth_headers
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        store = AuthStore(auth_file)
        store.save("anthropic", ApiKeyCredentials(api_key="sk-anthropic-key"))

        headers = get_auth_headers("anthropic")
        assert headers is not None
        assert headers["x-api-key"] == "sk-anthropic-key"

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

    def test_get_auth_headers_returns_none_if_not_authenticated(self, tmp_path, monkeypatch):
        """get_auth_headers returns None if no credentials."""
        from jdo.auth.api import get_auth_headers

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        headers = get_auth_headers("anthropic")
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

        # Store and then clear
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

        # Should not raise
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

    def test_save_credentials_stores_oauth(self, tmp_path, monkeypatch):
        """save_credentials stores OAuth credentials."""
        from jdo.auth.api import get_credentials, save_credentials
        from jdo.auth.models import OAuthCredentials

        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.api.get_auth_path", lambda: auth_file)

        expires = int(time.time() * 1000) + 3600000
        save_credentials(
            "anthropic",
            OAuthCredentials(
                access_token="access",
                refresh_token="refresh",
                expires_at=expires,
            ),
        )

        creds = get_credentials("anthropic")
        assert creds is not None
        assert isinstance(creds, OAuthCredentials)
        assert creds.access_token == "access"
