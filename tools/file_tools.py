"""Minimal workspace-scoped file reading tool for Mini Hermes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.registry import registry


DEFAULT_WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_SEARCH_DIRS = {".git", ".mini-hermes", ".venv", "__pycache__"}


def _within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def _unique_filename_match(filename: str, workspace_root: Path) -> Path | None:
    matches = [
        candidate
        for candidate in workspace_root.rglob(filename)
        if candidate.is_file()
        and not any(part in EXCLUDED_SEARCH_DIRS for part in candidate.parts)
        and _within(candidate, workspace_root)
    ]
    return matches[0] if len(matches) == 1 else None


def read_file(
    path: str,
    *,
    workspace_root: Path | str = DEFAULT_WORKSPACE_ROOT,
) -> str:
    """Read one complete UTF-8 text file inside *workspace_root*."""
    root = Path(workspace_root).resolve()
    relative = Path(path.strip())
    if not path.strip():
        return "read_file error: path is required"
    if relative.is_absolute() or ".." in relative.parts:
        return "read_file error: absolute paths and '..' are not allowed"

    target = root / relative
    if len(relative.parts) == 1 and not target.is_file():
        matched = _unique_filename_match(relative.name, root)
        if matched is not None:
            target = matched

    if not _within(target, root):
        return "read_file error: path must stay inside the Mini Hermes workspace"
    if not target.is_file():
        return f"read_file error: file not found or bare filename is ambiguous: {path}"

    try:
        content = target.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return f"read_file error: not a UTF-8 text file: {path}"
    relative_target = target.relative_to(root)
    return f"[File: {relative_target}]\n{content}"


READ_FILE_SCHEMA = {
    "description": (
        "Read a complete UTF-8 source or text file inside the Mini Hermes project. "
        "Use a workspace-relative path such as agent/skill_commands.py. A bare "
        "filename is accepted only when it uniquely identifies one project file."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Workspace-relative file path or unique bare filename.",
            }
        },
        "required": ["path"],
        "additionalProperties": False,
    },
}


def _handle_read_file(args: dict[str, Any]) -> str:
    return read_file(args["path"])


registry.register(
    name="read_file",
    toolset="files",
    schema=READ_FILE_SCHEMA,
    handler=_handle_read_file,
)
