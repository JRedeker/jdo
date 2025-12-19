"""Provider authentication registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class AuthMethod(Enum):
    """Authentication methods supported by providers."""

    API_KEY = auto()


@dataclass
class ProviderInfo:
    """Information about a provider.

    Attributes:
        name: Human-readable provider name.
        api_key_url: URL where users can obtain an API key.
        auth_methods: List of supported authentication methods.
        env_var: Environment variable name for API key.
    """

    name: str
    api_key_url: str
    auth_methods: list[AuthMethod]
    env_var: str


# Registry of supported providers
_PROVIDERS: dict[str, ProviderInfo] = {
    "openai": ProviderInfo(
        name="OpenAI",
        api_key_url="https://platform.openai.com/api-keys",
        auth_methods=[AuthMethod.API_KEY],
        env_var="OPENAI_API_KEY",
    ),
    "openrouter": ProviderInfo(
        name="OpenRouter",
        api_key_url="https://openrouter.ai/keys",
        auth_methods=[AuthMethod.API_KEY],
        env_var="OPENROUTER_API_KEY",
    ),
}


def get_auth_methods(provider_id: str) -> list[AuthMethod]:
    """Get supported authentication methods for a provider.

    Args:
        provider_id: The provider identifier.

    Returns:
        List of supported AuthMethod values, or empty list if unknown.
    """
    info = _PROVIDERS.get(provider_id)
    return info.auth_methods if info else []


def get_provider_info(provider_id: str) -> ProviderInfo | None:
    """Get information about a provider.

    Args:
        provider_id: The provider identifier.

    Returns:
        ProviderInfo if found, None otherwise.
    """
    return _PROVIDERS.get(provider_id)


def list_providers() -> list[str]:
    """List all registered provider IDs.

    Returns:
        List of provider ID strings.
    """
    return list(_PROVIDERS.keys())
