"""OAuth 2.0 PKCE flow implementation for Claude authentication."""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

import httpx

from jdo.ai.timeout import HTTP_TIMEOUT_SECONDS
from jdo.auth.models import OAuthCredentials
from jdo.exceptions import AuthError
from jdo.retry import http_retry

# OAuth Configuration (matching OpenCode's implementation)
CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"
AUTHORIZATION_URL = "https://claude.ai/oauth/authorize"
TOKEN_URL = "https://console.anthropic.com/v1/oauth/token"
REDIRECT_URI = "https://console.anthropic.com/oauth/code/callback"
SCOPES = "org:create_api_key user:profile user:inference"


class AuthenticationError(AuthError):
    """Raised when authentication fails."""


class TokenRevokedError(AuthenticationError):
    """Raised when a refresh token has been revoked."""


def generate_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code verifier and challenge.

    Returns:
        Tuple of (verifier, challenge) where:
        - verifier: 43-128 character URL-safe string
        - challenge: base64url-encoded SHA256 hash of verifier
    """
    # Generate 32 bytes of random data (results in 43 chars after base64)
    random_bytes = secrets.token_bytes(32)
    verifier = base64.urlsafe_b64encode(random_bytes).decode("ascii").rstrip("=")

    # Generate challenge: SHA256 hash of verifier, base64url encoded
    sha256_hash = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(sha256_hash).decode("ascii").rstrip("=")

    return verifier, challenge


def build_authorization_url() -> tuple[str, str]:
    """Build the OAuth authorization URL with PKCE challenge.

    Returns:
        Tuple of (authorization_url, verifier) where:
        - authorization_url: Complete URL to redirect user to
        - verifier: PKCE verifier to use in token exchange
    """
    verifier, challenge = generate_pkce_pair()

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": verifier,  # Use verifier as state for PKCE
    }

    url = f"{AUTHORIZATION_URL}?{urlencode(params)}"
    return url, verifier


@http_retry()
async def exchange_code(code: str, verifier: str) -> OAuthCredentials:
    """Exchange an authorization code for access tokens.

    Args:
        code: The authorization code from the OAuth callback.
              May contain state appended after '#' (e.g., "code#state").
        verifier: The PKCE verifier used when building the auth URL.

    Returns:
        OAuthCredentials with access token, refresh token, and expiry.

    Raises:
        AuthenticationError: If the exchange fails.
    """
    # Authorization code may have state appended after '#' separator
    code_parts = code.split("#")
    actual_code = code_parts[0]
    state = code_parts[1] if len(code_parts) > 1 else None

    # Build the request payload - using JSON format (not form-urlencoded)
    payload: dict[str, str] = {
        "grant_type": "authorization_code",
        "code": actual_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": verifier,
    }
    if state:
        payload["state"] = state

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                TOKEN_URL,
                json=payload,  # Use JSON, not form-urlencoded
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 401:
                raise AuthenticationError("Invalid authorization code")

            if not response.is_success:
                # Include response body for debugging OAuth errors
                error_detail = response.text
                raise AuthenticationError(
                    f"Token exchange failed (HTTP {response.status_code}): {error_detail}"
                )

            token_data = response.json()
            expires_at = int(time.time() * 1000) + (token_data["expires_in"] * 1000)

            return OAuthCredentials(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=expires_at,
            )

    except httpx.HTTPStatusError as e:
        # Include response body for debugging OAuth errors
        error_detail = getattr(e.response, "text", "")
        if error_detail:
            error_detail = f" - {error_detail}"
        raise AuthenticationError(f"Token exchange failed: {e}{error_detail}") from e
    except httpx.ConnectError as e:
        raise AuthenticationError(f"Network error during token exchange: {e}") from e


@http_retry()
async def refresh_tokens(refresh_token: str) -> OAuthCredentials:
    """Refresh OAuth tokens using a refresh token.

    Args:
        refresh_token: The refresh token from previous authentication.

    Returns:
        OAuthCredentials with new access token, refresh token, and expiry.

    Raises:
        TokenRevokedError: If the refresh token has been revoked.
        AuthenticationError: If refresh fails for other reasons.
    """
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
    }

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                TOKEN_URL,
                json=payload,  # Use JSON, not form-urlencoded
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 401:
                raise TokenRevokedError("Refresh token has been revoked")

            if not response.is_success:
                error_detail = response.text
                raise AuthenticationError(
                    f"Token refresh failed (HTTP {response.status_code}): {error_detail}"
                )

            token_data = response.json()
            expires_at = int(time.time() * 1000) + (token_data["expires_in"] * 1000)

            return OAuthCredentials(
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expires_at=expires_at,
            )

    except httpx.HTTPStatusError as e:
        raise AuthenticationError(f"Token refresh failed: {e}") from e
    except httpx.ConnectError as e:
        raise AuthenticationError(f"Network error during token refresh: {e}") from e
