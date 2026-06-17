from typing import Any

from citrus.providers.base import ModelRequest, ModelResponse, ToolSpec
from citrus.runtime.messages import Message, TextBlock, ToolCall


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, client: Any | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self._client = client

    def complete(self, request: ModelRequest) -> ModelResponse:
        client = self._client or self._build_client()
        kwargs: dict[str, object] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [
                {
                    "role": message.role,
                    "content": [
                        {"type": "text", "text": block.text}
                        for block in message.content
                        if isinstance(block, TextBlock)
                    ],
                }
                for message in request.messages
                if message.role in {"user", "assistant"}
            ],
        }
        if request.tools:
            kwargs["tools"] = [self._tool_to_anthropic(tool) for tool in request.tools]

        response = client.messages.create(**kwargs)
        messages: list[Message] = []
        for block in response.content:
            if getattr(block, "type", "text") == "tool_use":
                messages.append(
                    Message.assistant_tool_call(
                        ToolCall(
                            id=block.id,
                            name=block.name,
                            arguments=block.input,
                        )
                    )
                )
            else:
                messages.append(Message.assistant_text(block.text))
        return ModelResponse(messages=messages)

    def _tool_to_anthropic(self, tool: ToolSpec) -> dict[str, object]:
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }

    def _build_client(self) -> Any:
        from anthropic import Anthropic  # type: ignore[import-not-found]

        return Anthropic(api_key=self.api_key)
