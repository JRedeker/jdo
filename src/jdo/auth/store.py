"""Credential storage for authentication tokens."""

from __future__ import annotations

import contextlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from jdo.auth.models import ApiKeyCredentials, OAuthCredentials, ProviderAuth
from jdo.paths import get_auth_path


class AuthStore:
    """File-based storage for provider authentication credentials.

    Stores credentials in a JSON file with secure permissions (0600 on Unix).
    Supports multiple providers with different credential types.

    Attributes:
        path: Path to the auth.json file.
    """

    def __init__(self, path: Path | None = None) -> None:
        """Initialize the AuthStore.

        Args:
            path: Optional path to the auth file. If not provided,
                  uses get_auth_path() from jdo.paths.
        """
        self.path = path if path is not None else get_auth_path()
        self._adapter: TypeAdapter[OAuthCredentials | ApiKeyCredentials] = TypeAdapter(ProviderAuth)

    def _read_store(self) -> dict[str, dict[str, Any]]:
        """Read the current auth store from disk.

        Returns:
            Dictionary of provider_id -> credentials dict.
        """
        if not self.path.exists():
            return {}

        try:
            content = self.path.read_text()
            return json.loads(content) if content.strip() else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_store(self, data: dict[str, dict[str, Any]]) -> None:
        """Write the auth store to disk atomically with secure permissions.

        Uses write-to-temp-file + atomic rename to prevent data corruption
        if the process is interrupted during write (P10 idempotence).

        Args:
            data: Dictionary of provider_id -> credentials dict.
        """
        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Write to a temporary file first, then atomically rename
        # This ensures we never have a partially written auth file
        fd, tmp_path = tempfile.mkstemp(
            dir=self.path.parent,
            prefix=".auth_",
            suffix=".tmp",
        )
        tmp_file = Path(tmp_path)
        try:
            # Write content to temp file
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, indent=2)

            # Set secure permissions on Unix before rename
            if sys.platform != "win32":
                tmp_file.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600

            # Atomic rename (POSIX guarantees atomicity for rename on same filesystem)
            tmp_file.replace(self.path)
        except Exception:
            # Clean up temp file on failure
            with contextlib.suppress(OSError):
                tmp_file.unlink()
            raise

    def get(self, provider_id: str) -> OAuthCredentials | ApiKeyCredentials | None:
        """Get credentials for a provider.

        Args:
            provider_id: The provider identifier (e.g., "anthropic", "openai").

        Returns:
            The credentials if found, None otherwise.
        """
        store = self._read_store()
        if provider_id not in store:
            return None

        try:
            return self._adapter.validate_python(store[provider_id])
        except Exception:
            return None

    def save(
        self,
        provider_id: str,
        credentials: OAuthCredentials | ApiKeyCredentials,
    ) -> None:
        """Save credentials for a provider.

        Args:
            provider_id: The provider identifier (e.g., "anthropic", "openai").
            credentials: The credentials to save.
        """
        store = self._read_store()
        store[provider_id] = credentials.model_dump()
        self._write_store(store)

    def delete(self, provider_id: str) -> None:
        """Delete credentials for a provider.

        This operation is idempotent - it doesn't raise if the provider
        doesn't exist.

        Args:
            provider_id: The provider identifier to delete.
        """
        store = self._read_store()
        if provider_id in store:
            del store[provider_id]
            self._write_store(store)

    def list_providers(self) -> list[str]:
        """List all providers with stored credentials.

        Returns:
            List of provider IDs.
        """
        return list(self._read_store().keys())
