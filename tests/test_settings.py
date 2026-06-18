import pytest

from citrus.config.settings import (
    CitrusConfig,
    ProviderSettingsError,
    build_provider,
    load_config,
    resolve_provider_settings,
)
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
        build_provider("anthropic", model="claude-test", env={}, config=CitrusConfig())


def test_build_provider_rejects_unknown_provider() -> None:
    with pytest.raises(ProviderSettingsError, match="Unknown provider"):
        build_provider("unknown", model=None, env={})


def test_load_config_reads_toml_file(tmp_path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
provider = "openai"
model = "gpt-test"

[providers.openai]
api_key = "config-key"
model = "gpt-provider-test"
""",
        encoding="utf-8",
    )

    config = load_config(env={"CITRUS_CONFIG": str(config_path)})

    assert config.path == config_path
    assert config.provider == "openai"
    assert config.model == "gpt-test"
    assert config.providers["openai"].api_key == "config-key"
    assert config.providers["openai"].model == "gpt-provider-test"


def test_load_config_prefers_project_local_file(tmp_path) -> None:
    config_dir = tmp_path / ".citrus"
    config_dir.mkdir()
    config_path = config_dir / "config.toml"
    config_path.write_text(
        """
provider = "anthropic"

[providers.anthropic]
api_key = "local-key"
""",
        encoding="utf-8",
    )

    config = load_config(env={}, cwd=tmp_path)

    assert config.path == config_path
    assert config.provider == "anthropic"
    assert config.providers["anthropic"].api_key == "local-key"


def test_explicit_config_path_overrides_project_local_file(tmp_path) -> None:
    local_dir = tmp_path / ".citrus"
    local_dir.mkdir()
    (local_dir / "config.toml").write_text(
        'provider = "anthropic"\n',
        encoding="utf-8",
    )
    explicit_path = tmp_path / "other.toml"
    explicit_path.write_text(
        'provider = "openai"\n',
        encoding="utf-8",
    )

    config = load_config(env={"CITRUS_CONFIG": str(explicit_path)}, cwd=tmp_path)

    assert config.path == explicit_path
    assert config.provider == "openai"


def test_load_config_returns_defaults_when_file_is_missing(tmp_path) -> None:
    config = load_config(env={"CITRUS_CONFIG": str(tmp_path / "missing.toml")})

    assert config.provider == "fake"
    assert config.model is None
    assert config.providers == {}


def test_resolve_provider_settings_uses_config_file_values() -> None:
    config = CitrusConfig(
        provider="openai",
        model=None,
        providers={"openai": {"api_key": "config-key", "model": "gpt-config"}},
    )

    resolved = resolve_provider_settings(
        provider=None,
        model=None,
        config=config,
        env={},
    )

    assert resolved.provider == "openai"
    assert resolved.model == "gpt-config"
    assert resolved.api_key == "config-key"


def test_resolve_provider_settings_prefers_cli_and_environment() -> None:
    config = CitrusConfig(
        provider="openai",
        model="gpt-config",
        providers={"openai": {"api_key": "config-key"}},
    )

    resolved = resolve_provider_settings(
        provider="anthropic",
        model="claude-cli",
        config=config,
        env={"ANTHROPIC_API_KEY": "env-key"},
    )

    assert resolved.provider == "anthropic"
    assert resolved.model == "claude-cli"
    assert resolved.api_key == "env-key"


def test_build_provider_uses_config_file_key() -> None:
    config = CitrusConfig(
        providers={"anthropic": {"api_key": "config-key", "model": "claude-config"}},
    )

    provider = build_provider(
        "anthropic",
        model=None,
        env={},
        config=config,
    )

    assert isinstance(provider, AnthropicProvider)
    assert provider.api_key == "config-key"
    assert provider.model == "claude-config"
