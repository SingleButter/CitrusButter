from typing import Protocol

import pytest

from citrus.providers.anthropic import AnthropicProvider
from citrus.providers.base import ModelRequest, ModelResponse, ToolSpec
from citrus.providers.deepseek import DeepSeekProvider
from citrus.providers.fake import FakeProvider
from citrus.providers.openai import OpenAIProvider
from citrus.runtime.messages import Message, ToolCall


class _ProviderMetadata(Protocol):
    name: str

    def complete(self, request: ModelRequest) -> object:
        ...


@pytest.mark.parametrize(
    ("provider", "expected"),
    [
        (AnthropicProvider(api_key="test-key", model="claude-test"), "anthropic"),
        (OpenAIProvider(api_key="test-key", model="gpt-test"), "openai"),
        (DeepSeekProvider(api_key="test-key", model="deepseek-test"), "deepseek"),
    ],
)
def test_provider_adapters_expose_common_metadata(
    provider: _ProviderMetadata,
    expected: str,
) -> None:
    assert provider.name == expected
    assert callable(provider.complete)


class _OpenAIMessage:
    content = "openai response"


class _OpenAIChoice:
    message = _OpenAIMessage()


class _OpenAIResponse:
    choices = [_OpenAIChoice()]


class _OpenAICompletions:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def create(self, **kwargs: object) -> _OpenAIResponse:
        self.request = kwargs
        return _OpenAIResponse()


class _OpenAIClient:
    def __init__(self) -> None:
        completions = _OpenAICompletions()
        self.chat = type("Chat", (), {"completions": completions})()
        self.completions = completions


def test_openai_provider_maps_messages_through_chat_client() -> None:
    client = _OpenAIClient()
    provider = OpenAIProvider(api_key="test-key", model="gpt-test", client=client)

    response = provider.complete(ModelRequest(messages=[Message.user_text("hello")]))

    assert response.messages == [Message.assistant_text("openai response")]
    assert client.completions.request == {
        "model": "gpt-test",
        "messages": [{"role": "user", "content": "hello"}],
    }


class _OpenAIToolFunction:
    name = "write_file"
    arguments = '{"path": "note.txt", "content": "hello"}'


class _OpenAIToolCall:
    id = "call-1"
    function = _OpenAIToolFunction()


class _OpenAIToolMessage:
    content = None
    tool_calls = [_OpenAIToolCall()]


class _OpenAIToolChoice:
    message = _OpenAIToolMessage()


class _OpenAIToolResponse:
    choices = [_OpenAIToolChoice()]


class _OpenAIToolCompletions(_OpenAICompletions):
    def create(self, **kwargs: object) -> _OpenAIToolResponse:
        self.request = kwargs
        return _OpenAIToolResponse()


class _OpenAIToolClient:
    def __init__(self) -> None:
        completions = _OpenAIToolCompletions()
        self.chat = type("Chat", (), {"completions": completions})()
        self.completions = completions


def test_openai_provider_maps_tools_and_tool_calls() -> None:
    client = _OpenAIToolClient()
    provider = OpenAIProvider(api_key="test-key", model="gpt-test", client=client)

    response = provider.complete(
        ModelRequest(
            messages=[Message.user_text("write")],
            tools=[
                ToolSpec(
                    name="write_file",
                    description="Write file",
                    input_schema={"type": "object"},
                )
            ],
        )
    )

    assert client.completions.request["tools"] == [
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write file",
                "parameters": {"type": "object"},
            },
        }
    ]
    assert response.messages[0].tool_calls()[0].name == "write_file"
    assert response.messages[0].tool_calls()[0].arguments == {
        "path": "note.txt",
        "content": "hello",
    }


def test_openai_provider_maps_tool_results_with_tool_call_id() -> None:
    client = _OpenAIClient()
    provider = OpenAIProvider(api_key="test-key", model="gpt-test", client=client)

    provider.complete(
        ModelRequest(
            messages=[
                Message.user_text("write"),
                Message.assistant_tool_call(
                    ToolCall(
                        id="call-1",
                        name="write_file",
                        arguments={"path": "note.txt", "content": "hello"},
                    )
                ),
                Message.tool_text("call-1", "Wrote note.txt"),
            ],
        )
    )

    assert client.completions.request == {
        "model": "gpt-test",
        "messages": [
            {"role": "user", "content": "write"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call-1",
                        "type": "function",
                        "function": {
                            "name": "write_file",
                            "arguments": '{"path": "note.txt", "content": "hello"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call-1",
                "content": "Wrote note.txt",
            },
        ],
    }


def test_deepseek_provider_uses_openai_compatible_client() -> None:
    client = _OpenAIClient()
    provider = DeepSeekProvider(
        api_key="test-key",
        model="deepseek-test",
        client=client,
    )

    response = provider.complete(ModelRequest(messages=[Message.user_text("hello")]))

    assert response.messages == [Message.assistant_text("openai response")]
    assert provider.base_url == "https://api.deepseek.com"


class _AnthropicTextBlock:
    type = "text"
    text = "anthropic response"


class _AnthropicResponse:
    content = [_AnthropicTextBlock()]


class _AnthropicMessages:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def create(self, **kwargs: object) -> _AnthropicResponse:
        self.request = kwargs
        return _AnthropicResponse()


class _AnthropicClient:
    def __init__(self) -> None:
        self.messages = _AnthropicMessages()


def test_anthropic_provider_maps_messages_through_messages_client() -> None:
    client = _AnthropicClient()
    provider = AnthropicProvider(
        api_key="test-key",
        model="claude-test",
        client=client,
    )

    response = provider.complete(ModelRequest(messages=[Message.user_text("hello")]))

    assert response.messages == [Message.assistant_text("anthropic response")]
    assert client.messages.request == {
        "model": "claude-test",
        "max_tokens": 4096,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "hello"}]}
        ],
    }


class _AnthropicToolBlock:
    type = "tool_use"
    id = "call-1"
    name = "write_file"
    input = {"path": "note.txt", "content": "hello"}


class _AnthropicToolResponse:
    content = [_AnthropicToolBlock()]


class _AnthropicToolMessages(_AnthropicMessages):
    def create(self, **kwargs: object) -> _AnthropicToolResponse:
        self.request = kwargs
        return _AnthropicToolResponse()


class _AnthropicToolClient:
    def __init__(self) -> None:
        self.messages = _AnthropicToolMessages()


def test_anthropic_provider_maps_tools_and_tool_uses() -> None:
    client = _AnthropicToolClient()
    provider = AnthropicProvider(
        api_key="test-key",
        model="claude-test",
        client=client,
    )

    response = provider.complete(
        ModelRequest(
            messages=[Message.user_text("write")],
            tools=[
                ToolSpec(
                    name="write_file",
                    description="Write file",
                    input_schema={"type": "object"},
                )
            ],
        )
    )

    assert client.messages.request["tools"] == [
        {
            "name": "write_file",
            "description": "Write file",
            "input_schema": {"type": "object"},
        }
    ]
    assert response.messages[0].tool_calls()[0].name == "write_file"
    assert response.messages[0].tool_calls()[0].arguments == {
        "path": "note.txt",
        "content": "hello",
    }



def test_fake_provider_can_repeat_last_response() -> None:
    provider = FakeProvider(
        responses=[
            ModelResponse(messages=[Message.assistant_text("again")]),
        ],
        repeat_last=True,
    )

    first = provider.complete(ModelRequest(messages=[Message.user_text("one")]))
    second = provider.complete(ModelRequest(messages=[Message.user_text("two")]))

    assert first.messages[0].text() == "again"
    assert second.messages[0].text() == "again"
