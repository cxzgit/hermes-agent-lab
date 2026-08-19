"""Safe, on-demand Skill file loading for Mini Hermes."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from agent.skill_commands import DEFAULT_SKILLS_DIR, SUPPORT_DIRS, parse_frontmatter
from tools.registry import registry


def _within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
        return True
    except ValueError:
        return False


def _find_skill(name: str, skills_dir: Path) -> tuple[Path, Path] | None:
    if not name or Path(name).is_absolute() or ".." in Path(name).parts:
        return None
    direct = skills_dir / name / "SKILL.md"
    candidates: list[Path] = []
    if direct.is_file() and _within(direct, skills_dir):
        candidates.append(direct)
    for skill_md in skills_dir.rglob("SKILL.md") if skills_dir.exists() else []:
        if any(part in SUPPORT_DIRS for part in skill_md.relative_to(skills_dir).parts):
            continue
        content = skill_md.read_text(encoding="utf-8-sig")
        frontmatter, _ = parse_frontmatter(content)
        public_name = str(frontmatter.get("name") or skill_md.parent.name)
        if skill_md.parent.name == name or public_name == name:
            if skill_md not in candidates:
                candidates.append(skill_md)
    if len(candidates) != 1:
        return None
    skill_md = candidates[0]
    return skill_md.parent, skill_md


def skill_view(
    name: str,
    file_path: str | None = None,
    *,
    skills_dir: Path | str = DEFAULT_SKILLS_DIR,
) -> dict[str, Any]:
    """Read a Skill or one support file without escaping its directory."""
    root = Path(skills_dir).resolve()
    found = _find_skill(name.strip(), root)
    if found is None:
        return {"success": False, "error": f"Skill not found or ambiguous: {name}"}
    skill_dir, skill_md = found

    if file_path is not None:
        relative = Path(file_path)
        if relative.is_absolute() or ".." in relative.parts:
            return {"success": False, "error": "Path traversal is not allowed."}
        target = skill_dir / relative
        if not _within(target, skill_dir):
            return {"success": False, "error": "File must stay inside the Skill directory."}
        if not target.is_file():
            return {"success": False, "error": f"Supporting file not found: {file_path}"}
        return {
            "success": True,
            "name": name,
            "file": file_path,
            "content": target.read_text(encoding="utf-8-sig"),
        }

    raw_content = skill_md.read_text(encoding="utf-8-sig")
    frontmatter, _ = parse_frontmatter(raw_content)
    linked_files = [
        str(path.relative_to(skill_dir))
        for support_dir in sorted(SUPPORT_DIRS)
        if (skill_dir / support_dir).is_dir()
        for path in sorted((skill_dir / support_dir).rglob("*"))
        if path.is_file() and _within(path, skill_dir)
    ]
    return {
        "success": True,
        "name": str(frontmatter.get("name") or skill_dir.name),
        "description": str(frontmatter.get("description") or ""),
        "content": raw_content,
        "path": str(skill_md.relative_to(root)),
        "skill_dir": str(skill_dir),
        "linked_files": linked_files,
    }


SKILL_VIEW_SCHEMA = {
    "description": "Load a Skill or one of its supporting files.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Skill name or relative path."},
            "file_path": {
                "type": "string",
                "description": "Optional relative path inside the Skill directory.",
            },
        },
        "required": ["name"],
        "additionalProperties": False,
    },
}


def _handle_skill_view(args: dict[str, Any]) -> str:
    result = skill_view(args["name"], args.get("file_path"))
    return json.dumps(result, ensure_ascii=False)


registry.register(
    name="skill_view",
    toolset="skills",
    schema=SKILL_VIEW_SCHEMA,
    handler=_handle_skill_view,
)
