"""Agent loop: ask the model, execute requested tools, and continue."""

from __future__ import annotations

import json
from typing import Any

from agent.tool_executor import execute_tool_calls
from agent.turn_context import build_turn_context


def fake_model(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    """Simulate a model that can only call tools present in its schemas."""
    last_message = messages[-1]
    if last_message["role"] == "tool":
        return {
            "content": f"工具告诉我：{last_message['content']}",
            "tool_calls": [],
            "finish_reason": "stop",
        }

    user_text = str(last_message["content"])
    available_names = {tool["function"]["name"] for tool in tools}
    if (
        ("几点" in user_text or "时间" in user_text)
        and "get_current_time" in available_names
    ):
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


def run_conversation(
    agent: Any,
    user_message: str,
    conversation_history: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    context = build_turn_context(user_message, conversation_history)
    messages = context.messages
    final_response = ""
    api_call_count = 0

    while api_call_count < 3:
        api_call_count += 1
        print(
            f"[6] loop #{api_call_count}: sending {len(messages)} message(s) "
            f"and {len(agent.tools)} tool schema(s) to fake_model"
        )
        assistant_response = fake_model(messages, agent.tools)
        tool_calls = assistant_response["tool_calls"]

        if tool_calls:
            print(f"[7] model requested {len(tool_calls)} tool call(s)")
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_response["content"],
                    "tool_calls": tool_calls,
                }
            )
            execute_tool_calls(tool_calls, messages)
            print("[9] continue: return to the top of the Agent loop")
            continue

        final_response = assistant_response["content"]
        messages.append({"role": "assistant", "content": final_response})
        print("[7] no tool calls: save final response and break")
        break

    return {
        "final_response": final_response,
        "messages": messages,
        "api_calls": api_call_count,
    }

