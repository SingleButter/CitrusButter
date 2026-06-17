from pathlib import Path

from citrus.tools.base import ToolContext
from citrus.tools.local.read_file import ReadFileTool
from citrus.tools.local.search import SearchFilesTool
from citrus.tools.local.shell import RunShellTool
from citrus.tools.local.write_file import WriteFileTool


def test_file_tools_read_and_write_inside_workspace(tmp_path: Path) -> None:
    context = ToolContext(workspace=tmp_path)

    write_result = WriteFileTool().run(
        {"path": "src/example.txt", "content": "hello"},
        context,
    )
    read_result = ReadFileTool().run({"path": "src/example.txt"}, context)

    assert write_result.is_error is False
    assert read_result.content == "hello"


def test_file_tools_reject_paths_outside_workspace(tmp_path: Path) -> None:
    context = ToolContext(workspace=tmp_path)
    outside = tmp_path.parent / "outside.txt"

    result = WriteFileTool().run(
        {"path": str(outside), "content": "nope"},
        context,
    )

    assert result.is_error is True
    assert "outside workspace" in result.content


def test_search_files_finds_matching_text(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("alpha\nneedle\n")
    (tmp_path / "b.py").write_text("beta\n")
    context = ToolContext(workspace=tmp_path)

    result = SearchFilesTool().run({"query": "needle"}, context)

    assert result.is_error is False
    assert "a.py:2:needle" in result.content


def test_run_shell_executes_in_workspace(tmp_path: Path) -> None:
    context = ToolContext(workspace=tmp_path)

    result = RunShellTool().run({"command": "pwd"}, context)

    assert result.is_error is False
    assert result.content.strip() == str(tmp_path)

