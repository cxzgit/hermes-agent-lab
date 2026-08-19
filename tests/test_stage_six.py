import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from agent.skill_commands import (
    build_skill_invocation_message,
    scan_skill_commands,
)
from cli import HermesCLI
from tools.file_tools import read_file
from tools.skills_tool import skill_view


def write_skill(root: Path) -> None:
    skill_dir = root / "learning" / "demo-skill"
    (skill_dir / "references").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        "name: demo-skill\n"
        "description: Demonstrate Skill loading.\n"
        "---\n\n"
        "# Demo Skill\n\n"
        "Explain the task with one concrete example.\n",
        encoding="utf-8",
    )
    (skill_dir / "references" / "details.md").write_text(
        "supporting detail", encoding="utf-8"
    )


class EchoResponses:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = "skill received"
        part = SimpleNamespace(type="output_text", text=text)
        item = SimpleNamespace(type="message", content=[part])
        return SimpleNamespace(
            output=[item], output_text=text, status="completed", usage=None
        )


class StageSixTests(unittest.TestCase):
    def test_read_file_supports_relative_and_unique_bare_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "agent" / "example.py"
            source.parent.mkdir()
            source.write_text("answer = 42\n", encoding="utf-8")

            self.assertIn("answer = 42", read_file("agent/example.py", workspace_root=root))
            self.assertIn("answer = 42", read_file("example.py", workspace_root=root))

    def test_read_file_rejects_paths_outside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = read_file("../secret.txt", workspace_root=root)

            self.assertIn("not allowed", result)

    def test_scan_builds_light_slash_command_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_skill(root)
            commands = scan_skill_commands(root)

            self.assertEqual(commands["/demo-skill"]["name"], "demo-skill")
            self.assertEqual(
                commands["/demo-skill"]["identifier"], "learning\\demo-skill"
            )
            self.assertNotIn("content", commands["/demo-skill"])

    def test_skill_view_reads_support_file_and_blocks_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_skill(root)

            loaded = skill_view(
                "learning/demo-skill", "references/details.md", skills_dir=root
            )
            blocked = skill_view(
                "learning/demo-skill", "../secret.txt", skills_dir=root
            )

            self.assertTrue(loaded["success"])
            self.assertEqual(loaded["content"], "supporting detail")
            self.assertFalse(blocked["success"])

    def test_invocation_message_contains_skill_and_user_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_skill(root)
            commands = scan_skill_commands(root)

            message = build_skill_invocation_message(
                "/demo-skill", "explain transactions", commands
            )

            self.assertIn("# Demo Skill", message)
            self.assertIn("references\\details.md", message)
            self.assertIn("[User instruction]\nexplain transactions", message)

    def test_cli_expands_skill_before_normal_user_turn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills_dir = root / "skills"
            write_skill(skills_dir)
            responses = EchoResponses()
            client = SimpleNamespace(responses=responses)
            cli = HermesCLI(
                model="test-model",
                base_url="https://example.test/v1",
                client=client,
                db_path=root / "state.db",
                skills_dir=skills_dir,
            )

            expanded = cli.prepare_user_input("/demo-skill explain transactions")
            cli.chat(expanded)

            sent_user = [
                item for item in responses.calls[0]["input"]
                if item.get("role") == "user"
            ][-1]
            self.assertIn("# Demo Skill", sent_user["content"])
            self.assertIn("explain transactions", sent_user["content"])
            cli.close()


if __name__ == "__main__":
    unittest.main()
