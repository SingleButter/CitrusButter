from pathlib import Path

from typer.testing import CliRunner

from citrus.cli.app import app
from citrus.providers.base import ModelRequest, ModelResponse
from citrus.runtime.messages import Message, ToolCall

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


def test_cli_run_prompts_for_ask_permission_and_allows_tool(
    tmp_path,
    monkeypatch,
) -> None:
    class ToolCallingFakeProvider:
        name = "fake"

        def __init__(self, responses):
            self._responses = [
                ModelResponse(
                    messages=[
                        Message.assistant_tool_call(
                            ToolCall(
                                id="call-1",
                                name="write_file",
                                arguments={"path": "note.txt", "content": "hello"},
                            )
                        )
                    ]
                ),
                ModelResponse(messages=[Message.assistant_text("done")]),
            ]
            self._index = 0
            self.requests: list[ModelRequest] = []

        def complete(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            response = self._responses[self._index]
            self._index += 1
            return response

    monkeypatch.setattr("citrus.cli.app.FakeProvider", ToolCallingFakeProvider)

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["run", "write note", "--provider", "fake"],
        input="y\n",
    )
    written = Path("note.txt").read_text()

    assert result.exit_code == 0
    assert "Allow tool write_file?" in result.output
    assert "done" in result.output
    assert written == "hello"


def test_cli_run_prompts_for_ask_permission_and_denies_by_default(
    tmp_path,
    monkeypatch,
) -> None:
    class ToolCallingFakeProvider:
        name = "fake"

        def __init__(self, responses):
            self._responses = [
                ModelResponse(
                    messages=[
                        Message.assistant_tool_call(
                            ToolCall(
                                id="call-1",
                                name="write_file",
                                arguments={"path": "note.txt", "content": "hello"},
                            )
                        )
                    ]
                )
            ]
            self._index = 0

        def complete(self, request: ModelRequest) -> ModelResponse:
            response = self._responses[self._index]
            self._index += 1
            return response

    monkeypatch.setattr("citrus.cli.app.FakeProvider", ToolCallingFakeProvider)

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", "write note", "--provider", "fake"], input="\n")
    exists = Path("note.txt").exists()

    assert result.exit_code == 0
    assert "Allow tool write_file?" in result.output
    assert "denied" in result.output.lower()
    assert exists is False
