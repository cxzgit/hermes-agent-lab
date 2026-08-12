import unittest

from agent.turn_context import build_turn_context
from cli import HermesCLI


class StageOneTests(unittest.TestCase):
    def test_build_turn_context_does_not_mutate_original_history(self) -> None:
        history = [{"role": "assistant", "content": "old answer"}]
        context = build_turn_context("hello", history)
        self.assertEqual(history, [{"role": "assistant", "content": "old answer"}])
        self.assertEqual(context.messages[-1], {"role": "user", "content": "hello"})

    def test_cli_reuses_history_between_turns(self) -> None:
        cli = HermesCLI()
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
