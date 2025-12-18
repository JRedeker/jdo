"""Pydantic models for authentication credentials."""

from __future__ import annotations

import time
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class OAuthCredentials(BaseModel):
    """OAuth 2.0 credentials with access and refresh tokens.

    Attributes:
        type: Literal "oauth" for discriminated union.
        access_token: The OAuth access token.
        refresh_token: The OAuth refresh token for token renewal.
        expires_at: Token expiration time in milliseconds since epoch.
    """

    type: Literal["oauth"] = "oauth"
    access_token: str
    refresh_token: str
    expires_at: int  # milliseconds since epoch

    def is_expired(self) -> bool:
        """Check if the access token has expired.

        Returns:
            True if the token has expired, False otherwise.
        """
        current_time_ms = int(time.time() * 1000)
        return current_time_ms >= self.expires_at


class ApiKeyCredentials(BaseModel):
    """API key credentials for providers that use simple key authentication.

    Attributes:
        type: Literal "api" for discriminated union.
        api_key: The API key (must be non-empty).
    """

    type: Literal["api"] = "api"
    api_key: Annotated[str, Field(min_length=1)]


# Discriminated union for provider credentials
ProviderAuth = Annotated[
    OAuthCredentials | ApiKeyCredentials,
    Field(discriminator="type"),
]
