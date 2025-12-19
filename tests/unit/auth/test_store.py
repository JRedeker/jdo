"""Tests for AuthStore credential storage."""

import json
import stat
import sys
from pathlib import Path

import pytest


class TestAuthStoreCreation:
    """Tests for AuthStore file creation."""

    def test_auth_store_creates_file_if_not_exists(self, tmp_path, monkeypatch):
        """AuthStore creates auth.json if it doesn't exist."""
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        # Save some credentials to trigger file creation
        from jdo.auth.models import ApiKeyCredentials

        store.save("openai", ApiKeyCredentials(api_key="sk-test"))

        assert auth_file.exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions")
    def test_auth_store_creates_file_with_0600_permissions(self, tmp_path):
        """AuthStore creates file with 0600 permissions on Unix."""
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        from jdo.auth.models import ApiKeyCredentials

        store.save("openai", ApiKeyCredentials(api_key="sk-test"))

        # Check file permissions
        file_stat = auth_file.stat()
        file_mode = stat.S_IMODE(file_stat.st_mode)
        assert file_mode == 0o600

    def test_auth_store_uses_get_auth_path(self, tmp_path, monkeypatch):
        """AuthStore default uses get_auth_path() from paths module."""
        # Mock get_auth_path to return our temp path
        auth_file = tmp_path / "auth.json"
        monkeypatch.setattr("jdo.auth.store.get_auth_path", lambda: auth_file)

        from jdo.auth.store import AuthStore

        store = AuthStore()
        from jdo.auth.models import ApiKeyCredentials

        store.save("test", ApiKeyCredentials(api_key="sk-test"))

        assert auth_file.exists()


class TestAuthStoreReadWrite:
    """Tests for AuthStore read/write operations."""

    def test_auth_store_reads_credentials_by_provider_id(self, tmp_path):
        """AuthStore reads credentials by provider_id."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        # Save credentials
        original = ApiKeyCredentials(api_key="sk-test-key")
        store.save("openai", original)

        # Read back
        loaded = store.get("openai")
        assert loaded is not None
        assert isinstance(loaded, ApiKeyCredentials)
        assert loaded.api_key == "sk-test-key"

    def test_auth_store_writes_credentials_by_provider_id(self, tmp_path):
        """AuthStore writes credentials by provider_id."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        creds = ApiKeyCredentials(api_key="sk-12345")
        store.save("openai", creds)

        # Verify file content directly
        data = json.loads(auth_file.read_text())
        assert "openai" in data
        assert data["openai"]["api_key"] == "sk-12345"

    def test_auth_store_updates_existing_credentials(self, tmp_path):
        """AuthStore updates existing credentials."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        # Save initial credentials
        store.save("openai", ApiKeyCredentials(api_key="sk-old"))

        # Update with new credentials
        store.save("openai", ApiKeyCredentials(api_key="sk-new"))

        # Verify update
        loaded = store.get("openai")
        assert loaded is not None
        assert loaded.api_key == "sk-new"

    def test_auth_store_deletes_credentials_by_provider_id(self, tmp_path):
        """AuthStore deletes credentials by provider_id."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        # Save and then delete
        store.save("openai", ApiKeyCredentials(api_key="sk-test"))
        store.delete("openai")

        # Verify deletion
        assert store.get("openai") is None

    def test_auth_store_returns_none_for_unknown_provider(self, tmp_path):
        """AuthStore returns None for unknown provider."""
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        assert store.get("nonexistent") is None

    def test_auth_store_delete_is_idempotent(self, tmp_path):
        """AuthStore delete is idempotent (no error if not exists)."""
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        # Should not raise even though "unknown" doesn't exist
        store.delete("unknown")


class TestAuthStoreMultipleProviders:
    """Tests for multiple provider support."""

    def test_auth_store_stores_multiple_providers(self, tmp_path):
        """AuthStore can store credentials for multiple providers."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        store.save("openai", ApiKeyCredentials(api_key="sk-openai"))
        store.save("openrouter", ApiKeyCredentials(api_key="sk-openrouter"))

        assert store.get("openai") is not None
        assert store.get("openrouter") is not None

    def test_auth_store_update_preserves_other_providers(self, tmp_path):
        """Updating one provider's credentials doesn't affect others."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        # Save multiple providers
        store.save("openai", ApiKeyCredentials(api_key="sk-openai"))
        store.save("openrouter", ApiKeyCredentials(api_key="sk-openrouter"))

        # Update one
        store.save("openai", ApiKeyCredentials(api_key="sk-openai-new"))

        # Verify other is unchanged
        openrouter_creds = store.get("openrouter")
        assert openrouter_creds is not None
        assert openrouter_creds.api_key == "sk-openrouter"


class TestAuthStoreAtomicWrite:
    """Tests for atomic write operations (P10 idempotence)."""

    def test_atomic_write_no_partial_file_on_success(self, tmp_path):
        """Successful write produces valid JSON file without temp files."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        store.save("openai", ApiKeyCredentials(api_key="sk-test"))

        # File should exist and be valid JSON
        assert auth_file.exists()
        data = json.loads(auth_file.read_text())
        assert "openai" in data

        # No temp files should remain
        temp_files = list(tmp_path.glob(".auth_*.tmp"))
        assert len(temp_files) == 0

    def test_atomic_write_cleans_up_on_failure(self, tmp_path, monkeypatch):
        """Failed write cleans up temp file."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        # Make Path.replace raise an error after temp file is created
        original_replace = Path.replace

        def failing_replace(self, target):
            msg = "Simulated failure"
            raise OSError(msg)

        monkeypatch.setattr(Path, "replace", failing_replace)

        with pytest.raises(OSError, match="Simulated failure"):
            store.save("openai", ApiKeyCredentials(api_key="sk-test"))

        # No temp files should remain after failure
        temp_files = list(tmp_path.glob(".auth_*.tmp"))
        assert len(temp_files) == 0

    def test_atomic_write_preserves_existing_on_failure(self, tmp_path, monkeypatch):
        """Failed write preserves existing file content."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        # First, save initial data successfully
        store.save("openai", ApiKeyCredentials(api_key="sk-original"))

        # Now make the replace fail
        original_replace = Path.replace

        def failing_replace(self, target):
            msg = "Simulated failure"
            raise OSError(msg)

        monkeypatch.setattr(Path, "replace", failing_replace)

        # Try to update - should fail
        with pytest.raises(OSError, match="Simulated failure"):
            store.save("openai", ApiKeyCredentials(api_key="sk-new"))

        # Restore original replace for reading
        monkeypatch.undo()

        # Original data should still be intact
        loaded = store.get("openai")
        assert loaded is not None
        assert loaded.api_key == "sk-original"

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix file permissions")
    def test_atomic_write_preserves_permissions(self, tmp_path):
        """Atomic write preserves 0600 permissions on Unix."""
        from jdo.auth.models import ApiKeyCredentials
        from jdo.auth.store import AuthStore

        auth_file = tmp_path / "auth.json"
        store = AuthStore(auth_file)

        # Save initial
        store.save("openai", ApiKeyCredentials(api_key="sk-test"))
        initial_mode = stat.S_IMODE(auth_file.stat().st_mode)
        assert initial_mode == 0o600

        # Update
        store.save("openai", ApiKeyCredentials(api_key="sk-updated"))
        updated_mode = stat.S_IMODE(auth_file.stat().st_mode)
        assert updated_mode == 0o600
