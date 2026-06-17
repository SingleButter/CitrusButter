from citrus.runtime.messages import ToolResult
from citrus.tools.base import ToolContext
from citrus.tools.local.paths import resolve_workspace_path


class WriteFileTool:
    name = "write_file"
    description = "Write a text file inside the workspace."
    input_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    }

    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:
        try:
            path = resolve_workspace_path(context.workspace, str(input["path"]))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(input["content"]), encoding="utf-8")
            return ToolResult(
                tool_call_id=context.tool_call_id,
                content=f"Wrote {path.relative_to(context.workspace.resolve())}",
            )
        except Exception as exc:
            return ToolResult(
                tool_call_id=context.tool_call_id,
                content=str(exc),
                is_error=True,
            )
