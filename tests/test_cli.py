from typer.testing import CliRunner

from citrus.cli.app import app

runner = CliRunner()


def test_cli_help_shows_project_name() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "CitrusButter" in result.output


def test_cli_exposes_v1_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "run" in result.output
    assert "providers" in result.output
    assert "config" in result.output


def test_cli_run_uses_fake_provider() -> None:
    result = runner.invoke(
        app,
        ["run", "say hello", "--provider", "fake", "--fake-response", "hello"],
    )

    assert result.exit_code == 0
    assert "hello" in result.output


def test_cli_run_reports_missing_real_provider_key(tmp_path) -> None:
    result = runner.invoke(
        app,
        ["run", "say hello", "--provider", "anthropic"],
        env={"CITRUS_CONFIG": str(tmp_path / "missing.toml")},
    )

    assert result.exit_code != 0
    assert "ANTHROPIC_API_KEY" in result.output


def test_cli_providers_lists_v1_providers() -> None:
    result = runner.invoke(app, ["providers"])

    assert result.exit_code == 0
    assert "anthropic" in result.output
    assert "openai" in result.output
    assert "deepseek" in result.output
    assert "fake" in result.output


def test_cli_config_shows_environment_based_defaults(tmp_path) -> None:
    result = runner.invoke(
        app,
        ["config"],
        env={"CITRUS_CONFIG": str(tmp_path / "missing.toml")},
    )

    assert result.exit_code == 0
    assert "config=" in result.output
    assert "provider=fake" in result.output
    assert "model=" in result.output
    assert "Environment variables override config file values." in result.output


def test_cli_config_shows_config_file_values(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
provider = "openai"
model = "gpt-test"

[providers.openai]
api_key = "config-key"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("CITRUS_CONFIG", str(config_path))

    result = runner.invoke(app, ["config"])

    assert result.exit_code == 0
    assert str(config_path) in result.output
    assert "provider=openai" in result.output
    assert "model=gpt-test" in result.output
    assert "openai api_key=configured" in result.output


def test_cli_run_uses_config_file_for_real_provider(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
provider = "anthropic"
model = "claude-test"

[providers.anthropic]
api_key = "config-key"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("CITRUS_CONFIG", str(config_path))

    result = runner.invoke(app, ["run", "say hello"])

    assert result.exit_code != 2
