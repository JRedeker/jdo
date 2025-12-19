"""Tests for auth credential models."""

import pytest
from pydantic import ValidationError


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

    def test_api_key_credentials_rejects_empty_key(self):
        """ApiKeyCredentials rejects empty api_key."""
        from jdo.auth.models import ApiKeyCredentials

        with pytest.raises(ValidationError) as exc_info:
            ApiKeyCredentials(api_key="")
        assert "api_key" in str(exc_info.value)


class TestProviderAuth:
    """Tests for ProviderAuth type alias."""

    def test_provider_auth_accepts_api_key_credentials(self):
        """ProviderAuth correctly identifies api key credentials."""
        from jdo.auth.models import ApiKeyCredentials, ProviderAuth

        data = {"api_key": "sk-1234567890"}
        from pydantic import TypeAdapter

        adapter = TypeAdapter(ProviderAuth)
        creds = adapter.validate_python(data)
        assert isinstance(creds, ApiKeyCredentials)
