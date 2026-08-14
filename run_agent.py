"""Public Agent object, matching run_agent.py's forwarding pattern."""

from __future__ import annotations

from typing import Any

from model_tools import get_tool_definitions


class AIAgent:
    def __init__(self) -> None:
        self.tools = get_tool_definitions()
        self.valid_tool_names = {
            tool["function"]["name"] for tool in self.tools
        }

    def run_conversation(
        self,
        user_message: str,
        conversation_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        print("[4] AIAgent.run_conversation -> agent.conversation_loop")
        from agent.conversation_loop import run_conversation

        return run_conversation(
            self,
            user_message=user_message,
            conversation_history=conversation_history,
        )

