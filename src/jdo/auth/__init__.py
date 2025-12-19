"""Authentication module for AI provider credentials."""

from __future__ import annotations

from jdo.auth.api import (
    clear_credentials,
    get_auth_headers,
    get_credentials,
    is_authenticated,
    save_credentials,
)
from jdo.auth.models import ApiKeyCredentials, ProviderAuth
from jdo.auth.registry import (
    AuthMethod,
    ProviderInfo,
    get_auth_methods,
    get_provider_info,
    list_providers,
)
from jdo.auth.screens import ApiKeyScreen
from jdo.auth.store import AuthStore

__all__ = [
    "ApiKeyCredentials",
    "ApiKeyScreen",
    "AuthMethod",
    "AuthStore",
    "ProviderAuth",
    "ProviderInfo",
    "clear_credentials",
    "get_auth_headers",
    "get_auth_methods",
    "get_credentials",
    "get_provider_info",
    "is_authenticated",
    "list_providers",
    "save_credentials",
]
