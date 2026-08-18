import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cli import HermesCLI
from hermes_state import SessionDB


class EchoResponses:
    def __init__(self) -> None:
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        user_items = [item for item in kwargs["input"] if item.get("role") == "user"]
        text = f"echo: {user_items[-1]['content']}"
        part = SimpleNamespace(type="output_text", text=text)
        message = SimpleNamespace(type="message", content=[part])
        return SimpleNamespace(
            output=[message], output_text=text, status="completed", usage=None
        )


def echo_client():
    responses = EchoResponses()
    return SimpleNamespace(responses=responses), responses


class StageFiveTests(unittest.TestCase):
    def test_tool_messages_round_trip_in_insertion_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = SessionDB(Path(directory) / "state.db")
            db.create_session("session-1")
            expected = [
                {"role": "user", "content": "time?"},
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"id": "call-1", "name": "clock", "arguments": "{}"}
                    ],
                },
                {
                    "role": "tool",
                    "content": "10:00",
                    "tool_call_id": "call-1",
                    "name": "clock",
                },
                {"role": "assistant", "content": "It is 10:00."},
            ]

            self.assertEqual(db.append_messages_batch("session-1", expected), 4)
            self.assertEqual(db.get_messages_as_conversation("session-1"), expected)
            db.close()

    def test_batch_failure_rolls_back_every_message(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = SessionDB(Path(directory) / "state.db")
            db.create_session("session-1")
            messages = [
                {"role": "user", "content": "first insert runs"},
                {
                    "role": "assistant",
                    "content": "serialization fails",
                    "tool_calls": [{"arguments": {1, 2, 3}}],
                },
            ]

            with self.assertRaises(TypeError):
                db.append_messages_batch("session-1", messages)

            self.assertEqual(db.get_messages_as_conversation("session-1"), [])
            db.close()

    def test_new_cli_instance_resumes_persisted_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "state.db"
            first_client, _ = echo_client()
            first_cli = HermesCLI(
                model="test-model",
                base_url="https://example.test/v1",
                client=first_client,
                db_path=db_path,
            )
            session_id = first_cli.session_id
            first_cli.chat("first")
            first_cli.close()

            second_client, second_responses = echo_client()
            resumed_cli = HermesCLI(
                model="test-model",
                base_url="https://example.test/v1",
                client=second_client,
                db_path=db_path,
                session_id=session_id,
            )
            self.assertEqual(
                resumed_cli.conversation_history,
                [
                    {"role": "user", "content": "first"},
                    {"role": "assistant", "content": "echo: first"},
                ],
            )

            resumed_cli.chat("second")

            sent_input = second_responses.calls[0]["input"]
            self.assertEqual(
                [item.get("content") for item in sent_input if "content" in item],
                ["first", "echo: first", "second"],
            )
            resumed_cli.close()


if __name__ == "__main__":
    unittest.main()
