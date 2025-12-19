"""Tests for provider registry."""

from jdo.auth.registry import AuthMethod, get_auth_methods, get_provider_info


class TestProviderRegistry:
    """Tests for provider auth methods registry."""

    def test_openai_supports_api_key(self):
        """Registry maps openai to API key."""
        methods = get_auth_methods("openai")
        assert AuthMethod.API_KEY in methods

    def test_openrouter_supports_api_key(self):
        """Registry maps openrouter to API key."""
        methods = get_auth_methods("openrouter")
        assert AuthMethod.API_KEY in methods

    def test_get_auth_method_returns_correct_type(self):
        """get_auth_methods returns list of AuthMethod."""
        methods = get_auth_methods("openai")
        assert isinstance(methods, list)
        assert all(isinstance(m, AuthMethod) for m in methods)

    def test_unknown_provider_returns_empty_list(self):
        """Unknown provider returns empty auth methods list."""
        methods = get_auth_methods("unknown_provider")
        assert methods == []


class TestProviderInfo:
    """Tests for provider info retrieval."""

    def test_get_provider_info_openai(self):
        """Get provider info for openai."""
        info = get_provider_info("openai")
        assert info is not None
        assert info.name == "OpenAI"
        assert "platform.openai.com" in info.api_key_url

    def test_get_provider_info_openrouter(self):
        """Get provider info for openrouter."""
        info = get_provider_info("openrouter")
        assert info is not None
        assert info.name == "OpenRouter"
        assert "openrouter.ai" in info.api_key_url

    def test_get_provider_info_unknown(self):
        """Get provider info for unknown provider returns None."""
        info = get_provider_info("unknown_provider")
        assert info is None
