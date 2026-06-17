from typing import Any, Literal

from pydantic import BaseModel


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ToolCallBlock(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    tool_call: ToolCall


ContentBlock = TextBlock | ToolCallBlock


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: list[ContentBlock]

    @classmethod
    def user_text(cls, text: str) -> "Message":
        return cls(role="user", content=[TextBlock(text=text)])

    @classmethod
    def assistant_text(cls, text: str) -> "Message":
        return cls(role="assistant", content=[TextBlock(text=text)])

    @classmethod
    def assistant_tool_call(cls, tool_call: ToolCall) -> "Message":
        return cls(role="assistant", content=[ToolCallBlock(tool_call=tool_call)])

    @classmethod
    def tool_text(cls, tool_call_id: str, text: str) -> "Message":
        return cls(role="tool", content=[TextBlock(text=text)])

    def text(self) -> str:
        return "\n".join(
            block.text for block in self.content if isinstance(block, TextBlock)
        )

    def tool_calls(self) -> list[ToolCall]:
        return [
            block.tool_call
            for block in self.content
            if isinstance(block, ToolCallBlock)
        ]


class ToolResult(BaseModel):
    tool_call_id: str = ""
    content: str
    is_error: bool = False
