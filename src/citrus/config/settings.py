import tomllib
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, Field

from citrus.providers.anthropic import AnthropicProvider
from citrus.providers.base import ModelProvider
from citrus.providers.deepseek import DeepSeekProvider
from citrus.providers.openai import OpenAIProvider


class ProviderSettingsError(ValueError):
    pass


class ProviderConfig(BaseModel):
    api_key: str | None = None
    model: str | None = None
    base_url: str | None = None


class CitrusConfig(BaseModel):
    path: Path | None = None
    provider: str = "fake"
    model: str | None = None
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)


class ResolvedProviderSettings(BaseModel):
    provider: str
    model: str | None
    api_key: str | None
    base_url: str | None = None


def load_config(env: Mapping[str, str], cwd: Path | None = None) -> CitrusConfig:
    path = _config_path(env, cwd or Path.cwd())
    if not path.exists():
        return CitrusConfig(path=path)

    with path.open("rb") as file:
        data = tomllib.load(file)

    providers = {
        name: ProviderConfig.model_validate(config)
        for name, config in data.get("providers", {}).items()
    }
    return CitrusConfig(
        path=path,
        provider=data.get("provider", "fake"),
        model=data.get("model"),
        providers=providers,
    )


def resolve_provider_settings(
    provider: str | None,
    model: str | None,
    config: CitrusConfig,
    env: Mapping[str, str],
) -> ResolvedProviderSettings:
    selected_provider = (
        provider or env.get("CITRUS_PROVIDER") or config.provider
    ).lower()
    provider_config = config.providers.get(selected_provider, ProviderConfig())
    selected_model = (
        model
        or env.get("CITRUS_MODEL")
        or provider_config.model
        or config.model
        or _default_model(selected_provider)
    )
    api_key = _provider_api_key(selected_provider, provider_config, env)
    return ResolvedProviderSettings(
        provider=selected_provider,
        model=selected_model,
        api_key=api_key,
        base_url=provider_config.base_url,
    )


def build_provider(
    provider: str,
    model: str | None,
    env: Mapping[str, str],
    config: CitrusConfig | None = None,
) -> ModelProvider:
    resolved = resolve_provider_settings(
        provider=provider,
        model=model,
        config=config or load_config(env),
        env=env,
    )
    normalized = resolved.provider

    if normalized == "anthropic":
        return AnthropicProvider(
            api_key=_required_key(resolved, "ANTHROPIC_API_KEY"),
            model=resolved.model or "claude-sonnet-4-5",
        )

    if normalized == "openai":
        return OpenAIProvider(
            api_key=_required_key(resolved, "OPENAI_API_KEY"),
            model=resolved.model or "gpt-4.1",
            base_url=resolved.base_url,
        )

    if normalized == "deepseek":
        return DeepSeekProvider(
            api_key=_required_key(resolved, "DEEPSEEK_API_KEY"),
            model=resolved.model or "deepseek-chat",
            base_url=resolved.base_url,
        )

    raise ProviderSettingsError(f"Unknown provider: {provider}")


def _config_path(env: Mapping[str, str], cwd: Path) -> Path:
    explicit = env.get("CITRUS_CONFIG")
    if explicit:
        return Path(explicit).expanduser()
    project_local = cwd / ".citrus" / "config.toml"
    if project_local.exists():
        return project_local
    return Path.home() / ".config" / "citrus" / "config.toml"


def _provider_api_key(
    provider: str,
    provider_config: ProviderConfig,
    env: Mapping[str, str],
) -> str | None:
    env_key = _api_key_env_name(provider)
    if env_key and env.get(env_key):
        return env[env_key]
    return provider_config.api_key


def _api_key_env_name(provider: str) -> str | None:
    return {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }.get(provider)


def _default_model(provider: str) -> str | None:
    return {
        "anthropic": "claude-sonnet-4-5",
        "openai": "gpt-4.1",
        "deepseek": "deepseek-chat",
        "fake": None,
    }.get(provider)


def _required_key(resolved: ResolvedProviderSettings, env_name: str) -> str:
    if not resolved.api_key:
        raise ProviderSettingsError(
            f"Missing API key for {resolved.provider}. Set {env_name} "
            "or add api_key to the CitrusButter config file."
        )
    return resolved.api_key
