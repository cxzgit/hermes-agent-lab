"""Discover Skill commands and turn an invocation into a user message."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_SKILLS_DIR = Path(__file__).resolve().parents[1] / "skills"
SUPPORT_DIRS = {"references", "templates", "scripts", "assets"}


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Split optional YAML frontmatter from the Markdown body."""
    content = content.removeprefix("\ufeff")
    if not content.startswith("---\n"):
        return {}, content
    marker = content.find("\n---", 4)
    if marker == -1:
        return {}, content
    yaml_text = content[4:marker]
    body_start = marker + 4
    if content[body_start:body_start + 1] == "\n":
        body_start += 1
    try:
        parsed = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        parsed = {}
    return parsed if isinstance(parsed, dict) else {}, content[body_start:]


def _skill_files(skills_dir: Path) -> list[Path]:
    matches: list[Path] = []
    for skill_md in skills_dir.rglob("SKILL.md") if skills_dir.exists() else []:
        relative_parts = skill_md.relative_to(skills_dir).parts
        if any(part in SUPPORT_DIRS or part.startswith(".") for part in relative_parts):
            continue
        matches.append(skill_md)
    return sorted(matches)


def scan_skill_commands(
    skills_dir: Path | str = DEFAULT_SKILLS_DIR,
) -> dict[str, dict[str, str]]:
    """Build a light ``/command -> metadata`` index from installed Skills."""
    root = Path(skills_dir).resolve()
    commands: dict[str, dict[str, str]] = {}
    for skill_md in _skill_files(root):
        content = skill_md.read_text(encoding="utf-8-sig")
        frontmatter, body = parse_frontmatter(content)
        name = str(frontmatter.get("name") or skill_md.parent.name).strip()
        slug = name.lower().replace("_", "-").replace(" ", "-")
        if not slug:
            continue
        description = str(frontmatter.get("description") or "").strip()
        if not description:
            description = next(
                (line.strip()[:80] for line in body.splitlines()
                 if line.strip() and not line.lstrip().startswith("#")),
                f"Invoke the {name} skill",
            )
        command = f"/{slug}"
        if command in commands:
            raise ValueError(f"Duplicate Skill command: {command}")
        commands[command] = {
            "name": name,
            "description": description,
            "identifier": str(skill_md.parent.relative_to(root)),
            "skill_md_path": str(skill_md),
            "skill_dir": str(skill_md.parent),
            "skills_dir": str(root),
        }
    return commands


def build_skill_invocation_message(
    cmd_key: str,
    user_instruction: str,
    commands: dict[str, dict[str, str]],
) -> str | None:
    """Load one Skill and format it as ordinary user-message content."""
    skill_info = commands.get(cmd_key)
    if skill_info is None:
        return None
    from tools.skills_tool import skill_view

    loaded = skill_view(
        skill_info["identifier"],
        skills_dir=Path(skill_info["skills_dir"]),
    )
    if not loaded["success"]:
        return None

    skill_name = loaded["name"]
    skill_dir = Path(loaded["skill_dir"])
    parts = [
        f'[IMPORTANT: The user invoked the "{skill_name}" Skill. Follow the complete instructions loaded below.]',
        "",
        str(loaded["content"]).strip(),
        "",
        f"[Skill directory: {skill_dir}]",
        "Resolve relative paths in this Skill against that directory.",
    ]
    linked_files = loaded.get("linked_files") or []
    if linked_files:
        parts.extend(["", "[This Skill has supporting files:]"])
        parts.extend(f"- {path}" for path in linked_files)
        parts.append("Load a supporting file with skill_view(name, file_path).")
    if user_instruction:
        parts.extend(["", "[User instruction]", user_instruction])
    return "\n".join(parts)
