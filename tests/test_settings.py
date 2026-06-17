import pytest

from citrus.config.settings import ProviderSettingsError, build_provider
from citrus.providers.anthropic import AnthropicProvider
from citrus.providers.deepseek import DeepSeekProvider
from citrus.providers.openai import OpenAIProvider


def test_build_provider_uses_anthropic_environment() -> None:
    provider = build_provider(
        "anthropic",
        model="claude-test",
        env={"ANTHROPIC_API_KEY": "key"},
    )

    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-test"


def test_build_provider_uses_openai_environment() -> None:
    provider = build_provider(
        "openai",
        model="gpt-test",
        env={"OPENAI_API_KEY": "key"},
    )

    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "gpt-test"


def test_build_provider_uses_deepseek_environment() -> None:
    provider = build_provider(
        "deepseek",
        model="deepseek-test",
        env={"DEEPSEEK_API_KEY": "key"},
    )

    assert isinstance(provider, DeepSeekProvider)
    assert provider.model == "deepseek-test"


def test_build_provider_explains_missing_key() -> None:
    with pytest.raises(ProviderSettingsError, match="ANTHROPIC_API_KEY"):
        build_provider("anthropic", model="claude-test", env={})


def test_build_provider_rejects_unknown_provider() -> None:
    with pytest.raises(ProviderSettingsError, match="Unknown provider"):
        build_provider("unknown", model=None, env={})
