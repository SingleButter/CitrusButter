import json
from typing import Any

from citrus.providers.base import ModelRequest, ModelResponse, ToolSpec
from citrus.runtime.messages import Message, ToolCall


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = client

    def complete(self, request: ModelRequest) -> ModelResponse:
        client = self._client or self._build_client()
        kwargs: dict[str, object] = {
            "model": self.model,
            "messages": [
                self._message_to_openai(message) for message in request.messages
            ],
        }
        if request.tools:
            kwargs["tools"] = [self._tool_to_openai(tool) for tool in request.tools]

        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None) or []
        if tool_calls:
            return ModelResponse(
                messages=[
                    Message.assistant_tool_call(
                        ToolCall(
                            id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=json.loads(tool_call.function.arguments),
                        )
                    )
                    for tool_call in tool_calls
                ]
            )
        return ModelResponse(messages=[Message.assistant_text(message.content or "")])

    def _tool_to_openai(self, tool: ToolSpec) -> dict[str, object]:
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            },
        }

    def _message_to_openai(self, message: Message) -> dict[str, object]:
        if message.role == "tool":
            if not message.tool_call_id:
                raise ValueError("Tool messages require a tool_call_id.")
            return {
                "role": "tool",
                "tool_call_id": message.tool_call_id,
                "content": message.text(),
            }

        tool_calls = message.tool_calls()
        if tool_calls:
            return {
                "role": message.role,
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(tool_call.arguments),
                        },
                    }
                    for tool_call in tool_calls
                ],
            }

        return {"role": message.role, "content": message.text()}

    def _build_client(self) -> Any:
        from openai import OpenAI

        if self.base_url:
            return OpenAI(api_key=self.api_key, base_url=self.base_url)
        return OpenAI(api_key=self.api_key)
