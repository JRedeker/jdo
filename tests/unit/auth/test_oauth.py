"""Tests for OAuth PKCE flow implementation."""

import base64
import hashlib
import re
from urllib.parse import parse_qs, urlparse

import pytest


class TestPKCEGeneration:
    """Tests for PKCE verifier and challenge generation."""

    def test_generate_pkce_pair_returns_verifier_and_challenge(self):
        """generate_pkce_pair creates both verifier and challenge."""
        from jdo.auth.oauth import generate_pkce_pair

        verifier, challenge = generate_pkce_pair()

        assert verifier is not None
        assert challenge is not None
        assert isinstance(verifier, str)
        assert isinstance(challenge, str)

    def test_verifier_length_is_valid(self):
        """Verifier is 43-128 characters per OAuth spec."""
        from jdo.auth.oauth import generate_pkce_pair

        verifier, _ = generate_pkce_pair()

        assert 43 <= len(verifier) <= 128

    def test_verifier_is_url_safe(self):
        """Verifier uses only unreserved URL characters."""
        from jdo.auth.oauth import generate_pkce_pair

        verifier, _ = generate_pkce_pair()

        # URL-safe: A-Z, a-z, 0-9, -, ., _, ~
        assert re.match(r"^[A-Za-z0-9\-._~]+$", verifier)

    def test_challenge_is_base64url_sha256_of_verifier(self):
        """Challenge is base64url-encoded SHA256 of verifier."""
        from jdo.auth.oauth import generate_pkce_pair

        verifier, challenge = generate_pkce_pair()

        # Manually compute expected challenge
        sha256_hash = hashlib.sha256(verifier.encode("ascii")).digest()
        expected = base64.urlsafe_b64encode(sha256_hash).decode("ascii").rstrip("=")

        assert challenge == expected

    def test_generate_pkce_pair_is_unique(self):
        """Each call generates unique values."""
        from jdo.auth.oauth import generate_pkce_pair

        pairs = [generate_pkce_pair() for _ in range(5)]
        verifiers = [p[0] for p in pairs]
        challenges = [p[1] for p in pairs]

        assert len(set(verifiers)) == 5
        assert len(set(challenges)) == 5


class TestAuthorizationURL:
    """Tests for OAuth authorization URL building."""

    def test_build_authorization_url_includes_client_id(self):
        """Authorization URL includes correct client_id."""
        from jdo.auth.oauth import build_authorization_url

        url, _ = build_authorization_url()
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "client_id" in params
        assert params["client_id"][0] == "9d1c250a-e61b-44d9-88ed-5944d1962f5e"

    def test_build_authorization_url_includes_redirect_uri(self):
        """Authorization URL includes correct redirect_uri."""
        from jdo.auth.oauth import build_authorization_url

        url, _ = build_authorization_url()
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "redirect_uri" in params
        assert params["redirect_uri"][0] == "https://console.anthropic.com/oauth/code/callback"

    def test_build_authorization_url_includes_code_challenge(self):
        """Authorization URL includes code_challenge parameter."""
        from jdo.auth.oauth import build_authorization_url

        url, _ = build_authorization_url()
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "code_challenge" in params
        assert params["code_challenge_method"][0] == "S256"

    def test_build_authorization_url_includes_scope(self):
        """Authorization URL includes correct scopes."""
        from jdo.auth.oauth import build_authorization_url

        url, _ = build_authorization_url()
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "scope" in params
        scope = params["scope"][0]
        assert "org:create_api_key" in scope
        assert "user:profile" in scope
        assert "user:inference" in scope

    def test_build_authorization_url_includes_state(self):
        """Authorization URL includes state parameter (verifier for PKCE)."""
        from jdo.auth.oauth import build_authorization_url

        url, verifier = build_authorization_url()
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        assert "state" in params
        # State should be the verifier for later exchange
        assert params["state"][0] == verifier

    def test_build_authorization_url_returns_verifier(self):
        """build_authorization_url returns the verifier for code exchange."""
        from jdo.auth.oauth import build_authorization_url

        url, verifier = build_authorization_url()

        assert verifier is not None
        assert len(verifier) >= 43

    def test_build_authorization_url_uses_correct_base(self):
        """Authorization URL uses correct Anthropic base URL."""
        from jdo.auth.oauth import build_authorization_url

        url, _ = build_authorization_url()
        parsed = urlparse(url)

        assert parsed.scheme == "https"
        assert parsed.netloc == "claude.ai"
        assert parsed.path == "/oauth/authorize"


class TestTokenExchange:
    """Tests for OAuth token exchange."""

    @pytest.fixture
    def mock_token_response(self):
        """Mock successful token response."""
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

    @pytest.mark.asyncio
    async def test_exchange_code_sends_post_to_token_endpoint(
        self, httpx_mock, mock_token_response
    ):
        """exchange_code sends POST to correct token endpoint."""
        from jdo.auth.oauth import exchange_code

        httpx_mock.add_response(
            url="https://console.anthropic.com/v1/oauth/token",
            method="POST",
            json=mock_token_response,
        )

        await exchange_code("auth_code_123", "verifier_abc")

        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        assert requests[0].method == "POST"
        assert str(requests[0].url) == "https://console.anthropic.com/v1/oauth/token"

    @pytest.mark.asyncio
    async def test_exchange_code_includes_code_and_verifier(self, httpx_mock, mock_token_response):
        """exchange_code includes code and verifier in request."""
        import json

        from jdo.auth.oauth import exchange_code

        httpx_mock.add_response(
            url="https://console.anthropic.com/v1/oauth/token",
            method="POST",
            json=mock_token_response,
        )

        await exchange_code("auth_code_123", "verifier_abc")

        request = httpx_mock.get_requests()[0]
        # Request body is JSON
        body = json.loads(request.content.decode())
        assert body["code"] == "auth_code_123"
        assert body["code_verifier"] == "verifier_abc"
        assert body["grant_type"] == "authorization_code"

    @pytest.mark.asyncio
    async def test_exchange_code_returns_oauth_credentials(self, httpx_mock, mock_token_response):
        """exchange_code returns OAuthCredentials on success."""
        from jdo.auth.models import OAuthCredentials
        from jdo.auth.oauth import exchange_code

        httpx_mock.add_response(
            url="https://console.anthropic.com/v1/oauth/token",
            method="POST",
            json=mock_token_response,
        )

        creds = await exchange_code("auth_code_123", "verifier_abc")

        assert isinstance(creds, OAuthCredentials)
        assert creds.access_token == "test_access_token"
        assert creds.refresh_token == "test_refresh_token"

    @pytest.mark.asyncio
    async def test_exchange_code_raises_on_401(self, httpx_mock):
        """exchange_code raises error on 401 Unauthorized."""
        from jdo.auth.oauth import AuthenticationError, exchange_code

        httpx_mock.add_response(
            url="https://console.anthropic.com/v1/oauth/token",
            method="POST",
            status_code=401,
            json={"error": "invalid_grant"},
        )

        with pytest.raises(AuthenticationError):
            await exchange_code("invalid_code", "verifier")

    @pytest.mark.asyncio
    async def test_exchange_code_raises_on_network_failure(self, httpx_mock):
        """exchange_code raises error on network failure."""
        import httpx

        from jdo.auth.oauth import AuthenticationError, exchange_code

        httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

        with pytest.raises(AuthenticationError):
            await exchange_code("code", "verifier")

    @pytest.mark.asyncio
    async def test_exchange_code_handles_code_with_state(self, httpx_mock, mock_token_response):
        """exchange_code correctly parses code#state format."""
        import json

        from jdo.auth.oauth import exchange_code

        httpx_mock.add_response(
            url="https://console.anthropic.com/v1/oauth/token",
            method="POST",
            json=mock_token_response,
        )

        # Code with state appended after '#'
        await exchange_code("auth_code_123#state_value_xyz", "verifier_abc")

        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content.decode())
        # Should extract code before '#' and include state
        assert body["code"] == "auth_code_123"
        assert body["state"] == "state_value_xyz"
        assert body["code_verifier"] == "verifier_abc"

    @pytest.mark.asyncio
    async def test_exchange_code_without_state(self, httpx_mock, mock_token_response):
        """exchange_code works with code that has no state."""
        import json

        from jdo.auth.oauth import exchange_code

        httpx_mock.add_response(
            url="https://console.anthropic.com/v1/oauth/token",
            method="POST",
            json=mock_token_response,
        )

        # Code without state
        await exchange_code("auth_code_123", "verifier_abc")

        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content.decode())
        assert body["code"] == "auth_code_123"
        assert "state" not in body  # No state should be included


class TestTokenRefresh:
    """Tests for OAuth token refresh."""

    @pytest.fixture
    def mock_refresh_response(self):
        """Mock successful refresh response."""
        return {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

    @pytest.mark.asyncio
    async def test_refresh_tokens_sends_post_with_refresh_token(
        self, httpx_mock, mock_refresh_response
    ):
        """refresh_tokens sends POST with refresh_token grant."""
        import json

        from jdo.auth.oauth import refresh_tokens

        httpx_mock.add_response(
            url="https://console.anthropic.com/v1/oauth/token",
            method="POST",
            json=mock_refresh_response,
        )

        await refresh_tokens("old_refresh_token")

        request = httpx_mock.get_requests()[0]
        # Request body is JSON
        body = json.loads(request.content.decode())
        assert body["grant_type"] == "refresh_token"
        assert body["refresh_token"] == "old_refresh_token"

    @pytest.mark.asyncio
    async def test_refresh_tokens_returns_updated_credentials(
        self, httpx_mock, mock_refresh_response
    ):
        """refresh_tokens returns new OAuthCredentials."""
        from jdo.auth.models import OAuthCredentials
        from jdo.auth.oauth import refresh_tokens

        httpx_mock.add_response(
            url="https://console.anthropic.com/v1/oauth/token",
            method="POST",
            json=mock_refresh_response,
        )

        creds = await refresh_tokens("old_refresh_token")

        assert isinstance(creds, OAuthCredentials)
        assert creds.access_token == "new_access_token"
        assert creds.refresh_token == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_refresh_tokens_raises_on_401_revoked(self, httpx_mock):
        """refresh_tokens raises TokenRevokedError on 401."""
        from jdo.auth.oauth import TokenRevokedError, refresh_tokens

        httpx_mock.add_response(
            url="https://console.anthropic.com/v1/oauth/token",
            method="POST",
            status_code=401,
            json={"error": "invalid_grant"},
        )

        with pytest.raises(TokenRevokedError):
            await refresh_tokens("revoked_token")

    @pytest.mark.asyncio
    async def test_refresh_tokens_raises_on_network_failure(self, httpx_mock):
        """refresh_tokens raises error on network failure."""
        import httpx

        from jdo.auth.oauth import AuthenticationError, refresh_tokens

        httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

        with pytest.raises(AuthenticationError):
            await refresh_tokens("token")
