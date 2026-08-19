import unittest
import json
from types import SimpleNamespace

from run_agent import AIAgent


class ScriptedResponses:
    def create(self, **kwargs):
        last_item = kwargs["input"][-1]
        if last_item.get("type") == "function_call_output":
            text = f"工具告诉我：{last_item['output']}"
            part = SimpleNamespace(type="output_text", text=text)
            message = SimpleNamespace(type="message", content=[part])
            return SimpleNamespace(
                output=[message], output_text=text, status="completed", usage=None
            )

        user_text = str(last_item["content"])
        if "几点" in user_text or "时间" in user_text:
            call = SimpleNamespace(
                type="function_call",
                id="fc_get_current_time_1",
                call_id="call_get_current_time_1",
                name="get_current_time",
                arguments=json.dumps(
                    {"timezone": "Asia/Shanghai"}, ensure_ascii=False
                ),
            )
            return SimpleNamespace(
                output=[call], output_text="", status="completed", usage=None
            )

        text = f"我收到了：{user_text}"
        part = SimpleNamespace(type="output_text", text=text)
        message = SimpleNamespace(type="message", content=[part])
        return SimpleNamespace(
            output=[message], output_text=text, status="completed", usage=None
        )


class AlwaysToolResponses:
    def create(self, **kwargs):
        call = SimpleNamespace(
            type="function_call",
            id="fc_loop",
            call_id="call_loop",
            name="get_current_time",
            arguments=json.dumps({"timezone": "Asia/Shanghai"}),
        )
        return SimpleNamespace(
            output=[call], output_text="", status="completed", usage=None
        )


def scripted_agent():
    return AIAgent(
        model="test-model",
        base_url="https://example.test/v1",
        client=SimpleNamespace(responses=ScriptedResponses()),
    )


class StageTwoTests(unittest.TestCase):
    def test_iteration_limit_is_configurable(self) -> None:
        agent = AIAgent(
            model="test-model",
            base_url="https://example.test/v1",
            client=SimpleNamespace(responses=AlwaysToolResponses()),
            max_iterations=2,
        )

        result = agent.run_conversation("keep using tools")

        self.assertEqual(agent.max_iterations, 2)
        self.assertEqual(result["api_calls"], 2)

    def test_iteration_limit_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            AIAgent(
                model="test-model",
                base_url="https://example.test/v1",
                client=SimpleNamespace(responses=ScriptedResponses()),
                max_iterations=0,
            )

    def test_plain_response_finishes_after_one_model_call(self) -> None:
        result = scripted_agent().run_conversation("hello")
        self.assertEqual(result["api_calls"], 1)
        self.assertEqual(
            [message["role"] for message in result["messages"]],
            ["user", "assistant"],
        )

    def test_tool_response_continues_to_a_second_model_call(self) -> None:
        result = scripted_agent().run_conversation("现在几点？")
        self.assertEqual(result["api_calls"], 2)
        self.assertEqual(
            [message["role"] for message in result["messages"]],
            ["user", "assistant", "tool", "assistant"],
        )
        assistant_tool_call = result["messages"][1]["tool_calls"][0]
        tool_result = result["messages"][2]
        self.assertEqual(tool_result["tool_call_id"], assistant_tool_call["id"])
        self.assertIn("Asia/Shanghai 的时间是 ", result["final_response"])


if __name__ == "__main__":
    unittest.main()
