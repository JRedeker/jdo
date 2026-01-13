"""Public API for authentication operations."""

from __future__ import annotations

import os

from jdo.auth.models import ApiKeyCredentials
from jdo.auth.registry import get_provider_info
from jdo.auth.store import AuthStore
from jdo.paths import get_auth_path


def _get_store() -> AuthStore:
    """Get the default auth store."""
    return AuthStore(get_auth_path())


def get_credentials(
    provider_id: str,
) -> ApiKeyCredentials | None:
    """Get credentials for a provider.

    Checks stored credentials first, then falls back to environment variables.

    Args:
        provider_id: The provider identifier (e.g., "openai", "openrouter").

    Returns:
        Credentials if found, None otherwise.
    """
    store = _get_store()
    creds = store.get(provider_id)
    if creds is not None:
        return creds

    provider_info = get_provider_info(provider_id)
    if provider_info is not None:
        env_value = os.environ.get(provider_info.env_var)
        if env_value is not None:
            return ApiKeyCredentials(api_key=env_value)

    return None


def save_credentials(
    provider_id: str,
    credentials: ApiKeyCredentials,
) -> None:
    """Save credentials for a provider.

    Args:
        provider_id: The provider identifier.
        credentials: The credentials to save.
    """
    store = _get_store()
    store.save(provider_id, credentials)


def clear_credentials(provider_id: str) -> None:
    """Clear credentials for a provider.

    This operation is idempotent.

    Args:
        provider_id: The provider identifier to clear.
    """
    store = _get_store()
    store.delete(provider_id)


def is_authenticated(provider_id: str) -> bool:
    """Check if a provider has valid credentials.

    Args:
        provider_id: The provider identifier.

    Returns:
        True if credentials exist, False otherwise.
    """
    return get_credentials(provider_id) is not None


def get_auth_headers(provider_id: str) -> dict[str, str] | None:
    """Get HTTP authentication headers for a provider.

    Returns appropriate headers based on credential type:
    - API key (OpenAI/OpenRouter): Authorization: Bearer header

    Args:
        provider_id: The provider identifier.

    Returns:
        Dictionary of headers if authenticated, None otherwise.
    """
    creds = get_credentials(provider_id)
    if creds is None:
        return None

    # All providers use Bearer token format
    return {"Authorization": f"Bearer {creds.api_key}"}
