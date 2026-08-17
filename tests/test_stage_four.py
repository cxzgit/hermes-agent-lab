import unittest
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agent.transports.codex import ResponsesApiTransport
from hermes_cli.config import load_model_settings
from run_agent import AIAgent


class RecordingResponses:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class RecordingClient:
    def __init__(self, response):
        self.responses = RecordingResponses(response)


class StageFourTests(unittest.TestCase):
    def test_config_yaml_and_dotenv_have_separate_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config.yaml").write_text(
                "model:\n"
                "  name: test-model\n"
                "  base_url: https://example.test/v1\n",
                encoding="utf-8",
            )
            (root / ".env").write_text(
                "OPENAI_API_KEY=test-secret\n", encoding="utf-8"
            )
            with patch.dict(os.environ, {}, clear=True):
                settings = load_model_settings(root)
                self.assertEqual(os.environ["OPENAI_API_KEY"], "test-secret")

            self.assertEqual(settings.name, "test-model")
            self.assertEqual(settings.base_url, "https://example.test/v1")

    def test_build_kwargs_separates_instructions_and_input(self) -> None:
        transport = ResponsesApiTransport()
        kwargs = transport.build_kwargs(
            model="test-model",
            messages=[
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "hello"},
            ],
            tools=[],
        )
        self.assertEqual(kwargs["instructions"], "system prompt")
        self.assertEqual(kwargs["input"], [{"role": "user", "content": "hello"}])
        self.assertNotIn("tools", kwargs)

    def test_tool_history_becomes_responses_items(self) -> None:
        transport = ResponsesApiTransport()
        items = transport.convert_messages(
            [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"id": "call_1", "name": "demo", "arguments": "{}"}
                    ],
                },
                {
                    "role": "tool",
                    "tool_call_id": "call_1",
                    "name": "demo",
                    "content": "ok",
                },
            ]
        )
        self.assertEqual(items[0]["type"], "function_call")
        self.assertEqual(items[1]["type"], "function_call_output")
        self.assertEqual(items[0]["call_id"], items[1]["call_id"])

    def test_openai_provider_uses_responses_create(self) -> None:
        part = SimpleNamespace(type="output_text", text="real-shaped answer")
        item = SimpleNamespace(type="message", content=[part])
        response = SimpleNamespace(
            output=[item], output_text="real-shaped answer", status="completed", usage=None
        )
        client = RecordingClient(response)
        agent = AIAgent(
            model="test-model",
            base_url="https://example.test/v1",
            client=client,
        )

        result = agent.run_conversation("hello")

        self.assertEqual(result["final_response"], "real-shaped answer")
        self.assertEqual(len(client.responses.calls), 1)
        self.assertEqual(client.responses.calls[0]["model"], "test-model")


if __name__ == "__main__":
    unittest.main()
