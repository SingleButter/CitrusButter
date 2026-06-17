from citrus.runtime.messages import ToolResult
from citrus.tools.base import ToolContext
from citrus.tools.local.paths import resolve_workspace_path


class ReadFileTool:
    name = "read_file"
    description = "Read a text file inside the workspace."
    input_schema: dict[str, object] = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }

    def run(self, input: dict[str, object], context: ToolContext) -> ToolResult:
        try:
            path = resolve_workspace_path(context.workspace, str(input["path"]))
            return ToolResult(
                tool_call_id=context.tool_call_id,
                content=path.read_text(encoding="utf-8"),
            )
        except Exception as exc:
            return ToolResult(
                tool_call_id=context.tool_call_id,
                content=str(exc),
                is_error=True,
            )
