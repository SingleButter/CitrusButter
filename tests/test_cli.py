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


def test_cli_run_reports_missing_real_provider_key() -> None:
    result = runner.invoke(app, ["run", "say hello", "--provider", "anthropic"])

    assert result.exit_code != 0
    assert "ANTHROPIC_API_KEY" in result.output


def test_cli_providers_lists_v1_providers() -> None:
    result = runner.invoke(app, ["providers"])

    assert result.exit_code == 0
    assert "anthropic" in result.output
    assert "openai" in result.output
    assert "deepseek" in result.output
    assert "fake" in result.output


def test_cli_config_shows_environment_based_defaults() -> None:
    result = runner.invoke(app, ["config"])

    assert result.exit_code == 0
    assert "CITRUS_PROVIDER" in result.output
    assert "CITRUS_MODEL" in result.output
