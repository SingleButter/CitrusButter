from collections.abc import Mapping

from citrus.providers.anthropic import AnthropicProvider
from citrus.providers.base import ModelProvider
from citrus.providers.deepseek import DeepSeekProvider
from citrus.providers.openai import OpenAIProvider


class ProviderSettingsError(ValueError):
    pass


def build_provider(
    provider: str,
    model: str | None,
    env: Mapping[str, str],
) -> ModelProvider:
    normalized = provider.lower()

    if normalized == "anthropic":
        return AnthropicProvider(
            api_key=_required_env(env, "ANTHROPIC_API_KEY"),
            model=model or "claude-sonnet-4-5",
        )

    if normalized == "openai":
        return OpenAIProvider(
            api_key=_required_env(env, "OPENAI_API_KEY"),
            model=model or "gpt-4.1",
        )

    if normalized == "deepseek":
        return DeepSeekProvider(
            api_key=_required_env(env, "DEEPSEEK_API_KEY"),
            model=model or "deepseek-chat",
        )

    raise ProviderSettingsError(f"Unknown provider: {provider}")


def _required_env(env: Mapping[str, str], key: str) -> str:
    value = env.get(key)
    if not value:
        raise ProviderSettingsError(f"Missing required environment variable: {key}")
    return value

