import unittest
from types import SimpleNamespace

from agent.turn_context import build_turn_context
from cli import HermesCLI


class TextResponses:
    def create(self, **kwargs):
        user_text = kwargs["input"][-1]["content"]
        text = f"我收到了：{user_text}"
        part = SimpleNamespace(type="output_text", text=text)
        message = SimpleNamespace(type="message", content=[part])
        return SimpleNamespace(
            output=[message], output_text=text, status="completed", usage=None
        )


def text_client():
    return SimpleNamespace(responses=TextResponses())


class StageOneTests(unittest.TestCase):
    def test_build_turn_context_does_not_mutate_original_history(self) -> None:
        history = [{"role": "assistant", "content": "old answer"}]
        context = build_turn_context("hello", history)
        self.assertEqual(history, [{"role": "assistant", "content": "old answer"}])
        self.assertEqual(context.messages[-1], {"role": "user", "content": "hello"})

    def test_cli_reuses_history_between_turns(self) -> None:
        cli = HermesCLI(
            model="test-model",
            base_url="https://example.test/v1",
            client=text_client(),
        )
        cli.chat("first")
        cli.chat("second")
        self.assertEqual(
            cli.conversation_history,
            [
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "我收到了：first"},
                {"role": "user", "content": "second"},
                {"role": "assistant", "content": "我收到了：second"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
