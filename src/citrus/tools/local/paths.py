from pathlib import Path


def resolve_workspace_path(workspace: Path, path: str) -> Path:
    root = workspace.resolve()
    candidate = Path(path)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"Path is outside workspace: {path}")
    return resolved

