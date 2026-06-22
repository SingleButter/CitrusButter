import json
from pathlib import Path

from typer.testing import CliRunner

from citrus.cli import app as cli_app
from citrus.cli.app import app
from citrus.providers.base import ModelRequest, ModelResponse
from citrus.runtime.messages import Message, ToolCall

runner = CliRunner()


def _event_types(path: Path) -> list[str]:
    return [
        json.loads(line)["type"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


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


def test_cli_run_writes_default_session_log(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "run",
            "say hello",
            "--provider",
            "fake",
            "--fake-response",
            "hello",
            "--session-id",
            "run-1",
        ],
    )
    session_log = tmp_path / ".citrus" / "sessions" / "run-1.jsonl"

    assert result.exit_code == 0
    assert session_log.exists()
    assert "task_started" in _event_types(session_log)
    assert "task_completed" in _event_types(session_log)


def test_cli_run_writes_custom_session_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    session_dir = tmp_path / "custom-sessions"

    result = runner.invoke(
        app,
        [
            "run",
            "say hello",
            "--provider",
            "fake",
            "--session-dir",
            str(session_dir),
            "--session-id",
            "custom-1",
        ],
    )
    session_log = session_dir / "custom-1.jsonl"

    assert result.exit_code == 0
    assert session_log.exists()
    assert "task_completed" in _event_types(session_log)


def test_cli_run_no_session_log_avoids_persistent_output(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "run",
            "say hello",
            "--provider",
            "fake",
            "--no-session-log",
            "--session-id",
            "off-1",
        ],
    )

    assert result.exit_code == 0
    assert not (tmp_path / ".citrus" / "sessions" / "off-1.jsonl").exists()


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



def test_cli_chat_exits_on_exit_command() -> None:
    result = runner.invoke(
        app,
        ["chat", "--provider", "fake", "--fake-response", "hello"],
        input="exit\n",
    )

    assert result.exit_code == 0
    assert "Starting CitrusButter chat" in result.output
    assert "Goodbye." in result.output


def test_cli_chat_preserves_context_between_turns(monkeypatch, tmp_path) -> None:
    instances = []

    class ChatFakeProvider:
        name = "fake"

        def __init__(self, responses, repeat_last=False):
            self._responses = [
                ModelResponse(messages=[Message.assistant_text("first answer")]),
                ModelResponse(messages=[Message.assistant_text("second answer")]),
            ]
            self._index = 0
            self.requests: list[ModelRequest] = []
            instances.append(self)

        def complete(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            response = self._responses[self._index]
            self._index += 1
            return response

    monkeypatch.setattr("citrus.cli.app.FakeProvider", ChatFakeProvider)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["chat", "--provider", "fake"],
        input="first\nsecond\nexit\n",
    )

    assert result.exit_code == 0
    assert "first answer" in result.output
    assert "second answer" in result.output
    assert [message.text() for message in instances[0].requests[1].messages] == [
        "first",
        "first answer",
        "second",
    ]


def test_cli_chat_writes_multiple_turns_to_one_session_log(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "chat",
            "--provider",
            "fake",
            "--fake-response",
            "hello",
            "--session-id",
            "chat-1",
        ],
        input="first\nsecond\nexit\n",
    )
    session_log = tmp_path / ".citrus" / "sessions" / "chat-1.jsonl"
    event_types = _event_types(session_log)

    assert result.exit_code == 0
    assert session_log.exists()
    assert len(list((tmp_path / ".citrus" / "sessions").glob("*.jsonl"))) == 1
    assert event_types.count("task_started") == 2
    assert event_types.count("task_completed") == 2


def test_cli_chat_prompts_for_permission_and_continues(tmp_path, monkeypatch) -> None:
    class ToolCallingFakeProvider:
        name = "fake"

        def __init__(self, responses, repeat_last=False):
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
                ModelResponse(messages=[Message.assistant_text("after")]),
            ]
            self._index = 0

        def complete(self, request: ModelRequest) -> ModelResponse:
            response = self._responses[self._index]
            self._index += 1
            return response

    monkeypatch.setattr("citrus.cli.app.FakeProvider", ToolCallingFakeProvider)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["chat", "--provider", "fake"],
        input="write note\ny\nnext\nexit\n",
    )

    assert result.exit_code == 0
    assert "Allow tool write_file?" in result.output
    assert "done" in result.output
    assert "after" in result.output
    assert Path("note.txt").read_text() == "hello"


def test_cli_chat_keeps_running_after_failed_turn(tmp_path, monkeypatch) -> None:
    instances = []

    class FailingThenRecoveringProvider:
        name = "fake"

        def __init__(self, responses, repeat_last=False):
            self._responses = [
                ModelResponse(
                    messages=[
                        Message.assistant_tool_call(
                            ToolCall(
                                id="call-1",
                                name="run_shell",
                                arguments={"command": "rm -rf /tmp/example"},
                            )
                        )
                    ]
                ),
                ModelResponse(messages=[Message.assistant_text("recovered")]),
            ]
            self._index = 0
            self.requests: list[ModelRequest] = []
            instances.append(self)

        def complete(self, request: ModelRequest) -> ModelResponse:
            self.requests.append(request)
            response = self._responses[self._index]
            self._index += 1
            return response

    monkeypatch.setattr("citrus.cli.app.FakeProvider", FailingThenRecoveringProvider)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["chat", "--provider", "fake"],
        input="delete\nnext\nexit\n",
    )

    assert result.exit_code == 0
    assert "denied" in result.output.lower()
    assert "recovered" in result.output
    assert [message.text() for message in instances[0].requests[1].messages] == [
        "next"
    ]



def test_chat_input_uses_prompt_toolkit(monkeypatch) -> None:
    calls = []

    def fake_prompt(label: str) -> str:
        calls.append(label)
        return "你好"

    monkeypatch.setattr(cli_app, "prompt", fake_prompt)
    monkeypatch.setattr(cli_app.sys.stdin, "isatty", lambda: True)

    assert cli_app._read_chat_input() == "你好"
    assert calls == ["citrus> "]
