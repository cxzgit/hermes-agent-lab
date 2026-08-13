import unittest

from run_agent import AIAgent


class StageTwoTests(unittest.TestCase):
    def test_plain_response_finishes_after_one_model_call(self) -> None:
        result = AIAgent().run_conversation("hello")
        self.assertEqual(result["api_calls"], 1)
        self.assertEqual(
            [message["role"] for message in result["messages"]],
            ["user", "assistant"],
        )

    def test_tool_response_continues_to_a_second_model_call(self) -> None:
        result = AIAgent().run_conversation("现在几点？")
        self.assertEqual(result["api_calls"], 2)
        self.assertEqual(
            [message["role"] for message in result["messages"]],
            ["user", "assistant", "tool", "assistant"],
        )
        assistant_tool_call = result["messages"][1]["tool_calls"][0]
        tool_result = result["messages"][2]
        self.assertEqual(tool_result["tool_call_id"], assistant_tool_call["id"])
        self.assertIn("2026-08-13 10:00:00", result["final_response"])


if __name__ == "__main__":
    unittest.main()

