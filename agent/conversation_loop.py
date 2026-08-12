"""Tiny conversation loop without tools or a real model API."""

from __future__ import annotations

from typing import Any

from agent.turn_context import build_turn_context


def fake_model(messages: list[dict[str, str]]) -> str:
    """Free, deterministic replacement for an LLM API."""
    last_user_message = messages[-1]["content"]
    return f"我收到了：{last_user_message}"


def run_conversation(
    agent: Any,
    user_message: str,
    conversation_history: list[dict[str, str]] | None,
) -> dict[str, Any]:
    del agent  # Reserved for later stages where the loop needs agent state.
    context = build_turn_context(user_message, conversation_history)
    messages = context.messages
    print(f"[6] conversation_loop sends {len(messages)} message(s) to fake_model")
    final_response = fake_model(messages)
    messages.append({"role": "assistant", "content": final_response})
    return {"final_response": final_response, "messages": messages}

