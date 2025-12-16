"""Tests for auth credential models."""

import time

import pytest
from pydantic import ValidationError


class TestOAuthCredentials:
    """Tests for OAuthCredentials model."""

    def test_oauth_credentials_requires_access_token(self):
        """OAuthCredentials requires access_token field."""
        from jdo.auth.models import OAuthCredentials

        with pytest.raises(ValidationError) as exc_info:
            OAuthCredentials(
                refresh_token="refresh_abc",
                expires_at=int(time.time() * 1000) + 3600000,
            )
        assert "access_token" in str(exc_info.value)

    def test_oauth_credentials_requires_refresh_token(self):
        """OAuthCredentials requires refresh_token field."""
        from jdo.auth.models import OAuthCredentials

        with pytest.raises(ValidationError) as exc_info:
            OAuthCredentials(
                access_token="access_xyz",
                expires_at=int(time.time() * 1000) + 3600000,
            )
        assert "refresh_token" in str(exc_info.value)

    def test_oauth_credentials_requires_expires_at(self):
        """OAuthCredentials requires expires_at field."""
        from jdo.auth.models import OAuthCredentials

        with pytest.raises(ValidationError) as exc_info:
            OAuthCredentials(
                access_token="access_xyz",
                refresh_token="refresh_abc",
            )
        assert "expires_at" in str(exc_info.value)

    def test_oauth_credentials_valid(self):
        """OAuthCredentials accepts valid data."""
        from jdo.auth.models import OAuthCredentials

        expires = int(time.time() * 1000) + 3600000
        creds = OAuthCredentials(
            access_token="access_xyz",
            refresh_token="refresh_abc",
            expires_at=expires,
        )
        assert creds.access_token == "access_xyz"
        assert creds.refresh_token == "refresh_abc"
        assert creds.expires_at == expires
        assert creds.type == "oauth"

    def test_oauth_credentials_is_expired_false_for_future(self):
        """is_expired returns False when token expires in the future."""
        from jdo.auth.models import OAuthCredentials

        # Expires 1 hour from now
        expires = int(time.time() * 1000) + 3600000
        creds = OAuthCredentials(
            access_token="access_xyz",
            refresh_token="refresh_abc",
            expires_at=expires,
        )
        assert creds.is_expired() is False

    def test_oauth_credentials_is_expired_true_for_past(self):
        """is_expired returns True when token has expired."""
        from jdo.auth.models import OAuthCredentials

        # Expired 1 hour ago
        expires = int(time.time() * 1000) - 3600000
        creds = OAuthCredentials(
            access_token="access_xyz",
            refresh_token="refresh_abc",
            expires_at=expires,
        )
        assert creds.is_expired() is True


class TestApiKeyCredentials:
    """Tests for ApiKeyCredentials model."""

    def test_api_key_credentials_requires_api_key(self):
        """ApiKeyCredentials requires api_key field."""
        from jdo.auth.models import ApiKeyCredentials

        with pytest.raises(ValidationError) as exc_info:
            ApiKeyCredentials()
        assert "api_key" in str(exc_info.value)

    def test_api_key_credentials_valid(self):
        """ApiKeyCredentials accepts valid data."""
        from jdo.auth.models import ApiKeyCredentials

        creds = ApiKeyCredentials(api_key="sk-1234567890")
        assert creds.api_key == "sk-1234567890"
        assert creds.type == "api"

    def test_api_key_credentials_rejects_empty_key(self):
        """ApiKeyCredentials rejects empty api_key."""
        from jdo.auth.models import ApiKeyCredentials

        with pytest.raises(ValidationError) as exc_info:
            ApiKeyCredentials(api_key="")
        assert "api_key" in str(exc_info.value)


class TestProviderAuth:
    """Tests for ProviderAuth discriminated union."""

    def test_provider_auth_selects_oauth_type(self):
        """ProviderAuth correctly identifies oauth credentials."""
        from jdo.auth.models import OAuthCredentials, ProviderAuth

        data = {
            "type": "oauth",
            "access_token": "access_xyz",
            "refresh_token": "refresh_abc",
            "expires_at": int(time.time() * 1000) + 3600000,
        }
        # Use TypeAdapter to validate the union
        from pydantic import TypeAdapter

        adapter = TypeAdapter(ProviderAuth)
        creds = adapter.validate_python(data)
        assert isinstance(creds, OAuthCredentials)
        assert creds.type == "oauth"

    def test_provider_auth_selects_api_type(self):
        """ProviderAuth correctly identifies api key credentials."""
        from jdo.auth.models import ApiKeyCredentials, ProviderAuth

        data = {
            "type": "api",
            "api_key": "sk-1234567890",
        }
        from pydantic import TypeAdapter

        adapter = TypeAdapter(ProviderAuth)
        creds = adapter.validate_python(data)
        assert isinstance(creds, ApiKeyCredentials)
        assert creds.type == "api"

    def test_provider_auth_rejects_invalid_type(self):
        """ProviderAuth rejects unknown credential types."""
        from jdo.auth.models import ProviderAuth

        data = {
            "type": "unknown",
            "some_field": "value",
        }
        from pydantic import TypeAdapter, ValidationError

        adapter = TypeAdapter(ProviderAuth)
        with pytest.raises(ValidationError):
            adapter.validate_python(data)
