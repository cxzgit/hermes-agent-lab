"""Agent loop: ask the active provider, execute requested tools, and continue."""

from __future__ import annotations

from typing import Any

from agent.tool_executor import execute_tool_calls
from agent.turn_context import build_turn_context


def run_conversation(
    agent: Any,
    user_message: str,
    conversation_history: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    context = build_turn_context(user_message, conversation_history)
    messages = context.messages
    final_response = ""
    api_call_count = 0

    while api_call_count < agent.max_iterations:
        api_call_count += 1
        print(
            f"[6] loop #{api_call_count}: sending {len(messages)} message(s) "
            f"and {len(agent.tools)} tool schema(s) to {agent.provider}"
        )
        api_kwargs = agent._build_api_kwargs(messages)
        raw_response = agent._perform_api_call(api_kwargs)
        assistant_response = agent._normalize_response(raw_response)
        tool_calls = [
            {
                "id": tool_call.id,
                "name": tool_call.name,
                "arguments": tool_call.arguments,
            }
            for tool_call in assistant_response.tool_calls or []
        ]

        if tool_calls:
            print(f"[7] model requested {len(tool_calls)} tool call(s)")
            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_response.content or "",
                    "tool_calls": tool_calls,
                }
            )
            execute_tool_calls(tool_calls, messages)
            print("[9] continue: return to the top of the Agent loop")
            continue

        final_response = assistant_response.content or ""
        messages.append({"role": "assistant", "content": final_response})
        print("[7] no tool calls: save final response and break")
        break

    return {
        "final_response": final_response,
        "messages": messages,
        "api_calls": api_call_count,
    }
