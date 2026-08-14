"""Turn model tool calls into Tool messages."""

from __future__ import annotations

import json
from typing import Any

from model_tools import handle_function_call


def execute_tool_calls(
    tool_calls: list[dict[str, Any]],
    messages: list[dict[str, Any]],
) -> None:
    for tool_call in tool_calls:
        try:
            arguments = json.loads(tool_call["arguments"])
        except json.JSONDecodeError as exc:
            tool_result = f"Invalid tool arguments: {exc}"
        else:
            tool_result = handle_function_call(tool_call["name"], arguments)

        tool_msg = {
            "role": "tool",
            "name": tool_call["name"],
            "tool_call_id": tool_call["id"],
            "content": tool_result,
        }
        messages.append(tool_msg)
        print(f"[8] tool_executor appended: {tool_msg}")

