"""Authentication module for AI provider credentials."""

from jdo.auth.api import (
    clear_credentials,
    get_auth_headers,
    get_credentials,
    is_authenticated,
    save_credentials,
)
from jdo.auth.models import ApiKeyCredentials, OAuthCredentials, ProviderAuth
from jdo.auth.oauth import (
    AuthenticationError,
    TokenRevokedError,
    build_authorization_url,
    exchange_code,
    refresh_tokens,
)
from jdo.auth.registry import (
    AuthMethod,
    ProviderInfo,
    get_auth_methods,
    get_provider_info,
    list_providers,
)
from jdo.auth.screens import ApiKeyScreen, OAuthScreen
from jdo.auth.store import AuthStore

__all__ = [
    "ApiKeyCredentials",
    "ApiKeyScreen",
    "AuthMethod",
    "AuthStore",
    "AuthenticationError",
    "OAuthCredentials",
    "OAuthScreen",
    "ProviderAuth",
    "ProviderInfo",
    "TokenRevokedError",
    "build_authorization_url",
    "clear_credentials",
    "exchange_code",
    "get_auth_headers",
    "get_auth_methods",
    "get_credentials",
    "get_provider_info",
    "is_authenticated",
    "list_providers",
    "refresh_tokens",
    "save_credentials",
]
