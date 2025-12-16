"""Tests for provider registry."""

from jdo.auth.registry import AuthMethod, get_auth_methods, get_provider_info


class TestProviderRegistry:
    """Tests for provider auth methods registry."""

    def test_anthropic_supports_oauth(self):
        """Registry maps anthropic to OAuth."""
        methods = get_auth_methods("anthropic")
        assert AuthMethod.OAUTH in methods

    def test_anthropic_supports_api_key(self):
        """Registry maps anthropic to API key."""
        methods = get_auth_methods("anthropic")
        assert AuthMethod.API_KEY in methods

    def test_openai_supports_api_key(self):
        """Registry maps openai to API key."""
        methods = get_auth_methods("openai")
        assert AuthMethod.API_KEY in methods

    def test_openai_does_not_support_oauth(self):
        """OpenAI does not support OAuth."""
        methods = get_auth_methods("openai")
        assert AuthMethod.OAUTH not in methods

    def test_openrouter_supports_api_key(self):
        """Registry maps openrouter to API key."""
        methods = get_auth_methods("openrouter")
        assert AuthMethod.API_KEY in methods

    def test_openrouter_does_not_support_oauth(self):
        """OpenRouter does not support OAuth."""
        methods = get_auth_methods("openrouter")
        assert AuthMethod.OAUTH not in methods

    def test_get_auth_method_returns_correct_type(self):
        """get_auth_methods returns list of AuthMethod."""
        methods = get_auth_methods("anthropic")
        assert isinstance(methods, list)
        assert all(isinstance(m, AuthMethod) for m in methods)


class TestProviderInfo:
    """Tests for provider info retrieval."""

    def test_get_provider_info_anthropic(self):
        """Get provider info for anthropic."""
        info = get_provider_info("anthropic")
        assert info is not None
        assert info.name == "Anthropic (Claude)"
        assert "console.anthropic.com" in info.api_key_url

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
