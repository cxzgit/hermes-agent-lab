"""Convert raw input into model-style messages."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TurnContext:
    messages: list[dict[str, str]]


def build_turn_context(
    user_message: str,
    conversation_history: list[dict[str, str]] | None,
) -> TurnContext:
    # Copy the outer list so append does not mutate the caller's list.
    messages = list(conversation_history) if conversation_history else []
    user_msg = {"role": "user", "content": user_message}
    messages.append(user_msg)
    print(f"[5] build_turn_context created: {user_msg}")
    return TurnContext(messages=messages)

