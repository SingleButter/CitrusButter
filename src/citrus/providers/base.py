from typing import Protocol

from pydantic import BaseModel, Field

from citrus.runtime.messages import Message


class ToolSpec(BaseModel):
    name: str
    description: str
    input_schema: dict[str, object]


class ModelRequest(BaseModel):
    messages: list[Message]
    tools: list[ToolSpec] = Field(default_factory=list)
    model: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    messages: list[Message]
    metadata: dict[str, str] = Field(default_factory=dict)


class ModelProvider(Protocol):
    name: str

    def complete(self, request: ModelRequest) -> ModelResponse:
        ...
