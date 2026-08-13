"""A small Agent loop that demonstrates text responses and tool calls."""

from __future__ import annotations

import json
from typing import Any

from agent.turn_context import build_turn_context


def fake_model(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Return a normalized Assistant response without using a real LLM API."""
    last_message = messages[-1]

    # After receiving a tool result, the model can write its final answer.
    if last_message["role"] == "tool":
        return {
            "content": f"工具告诉我：{last_message['content']}",
            "tool_calls": [],
            "finish_reason": "stop",
        }

    user_text = str(last_message["content"])
    if "几点" in user_text or "时间" in user_text:
        return {
            "content": "我先查询时间。",
            "tool_calls": [
                {
                    "id": "call_get_current_time_1",
                    "name": "get_current_time",
                    "arguments": json.dumps(
                        {"timezone": "Asia/Shanghai"}, ensure_ascii=False
                    ),
                }
            ],
            "finish_reason": "tool_calls",
        }

    return {
        "content": f"我收到了：{user_text}",
        "tool_calls": [],
        "finish_reason": "stop",
    }


def execute_tool_call(tool_call: dict[str, Any]) -> str:
    """Execute one built-in teaching tool.

    Stage three will replace this condition with a real tool registry.
    """
    arguments = json.loads(tool_call["arguments"])
    if tool_call["name"] == "get_current_time":
        timezone = arguments["timezone"]
        return f"{timezone} 的时间是 2026-08-13 10:00:00"
    return f"未知工具：{tool_call['name']}"


def run_conversation(
    agent: Any,
    user_message: str,
    conversation_history: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    del agent  # Reserved for later stages where the loop needs agent state.
    context = build_turn_context(user_message, conversation_history)
    messages = context.messages
    final_response = ""
    api_call_count = 0

    # Real Hermes also has iteration and budget limits. Three iterations are
    # enough for this exercise and prevent an accidental infinite loop.
    while api_call_count < 3:
        api_call_count += 1
        print(
            f"[6] loop #{api_call_count}: sending {len(messages)} message(s) "
            "to fake_model"
        )
        assistant_response = fake_model(messages)
        tool_calls = assistant_response["tool_calls"]

        if tool_calls:
            print(f"[7] model requested {len(tool_calls)} tool call(s)")
            assistant_msg = {
                "role": "assistant",
                "content": assistant_response["content"],
                "tool_calls": tool_calls,
            }
            messages.append(assistant_msg)

            for tool_call in tool_calls:
                tool_result = execute_tool_call(tool_call)
                tool_msg = {
                    "role": "tool",
                    "name": tool_call["name"],
                    "tool_call_id": tool_call["id"],
                    "content": tool_result,
                }
                messages.append(tool_msg)
                print(f"[8] tool result appended: {tool_msg}")

            print("[9] continue: return to the top of the Agent loop")
            continue

        # No tool calls means the model has produced the final text response.
        final_response = assistant_response["content"]
        messages.append({"role": "assistant", "content": final_response})
        print("[7] no tool calls: save final response and break")
        break

    return {
        "final_response": final_response,
        "messages": messages,
        "api_calls": api_call_count,
    }

