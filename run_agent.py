"""Public Agent object, matching run_agent.py's forwarding pattern."""

from __future__ import annotations

import os
from typing import Any

from agent.transports.codex import ResponsesApiTransport
from model_tools import get_tool_definitions


class AIAgent:
    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key: str | None = None,
        client: Any = None,
    ) -> None:
        self.provider = "openai"
        self.model = model
        self.base_url = base_url
        self.api_mode = "codex_responses"
        self.tools = get_tool_definitions()
        self.valid_tool_names = {
            tool["function"]["name"] for tool in self.tools
        }
        self.transport = ResponsesApiTransport()
        self.client = client or self._create_client(api_key)

    def _create_client(self, api_key: str | None) -> Any:
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise RuntimeError(
                "OPENAI_API_KEY is missing. Put it in the project's .env file; "
                "do not put the key in source code or config.yaml."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI support is not installed. Run: pip install -e '.[openai]'"
            ) from exc
        return OpenAI(api_key=resolved_key, base_url=self.base_url)

    def _build_api_kwargs(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return self.transport.build_kwargs(
            model=self.model,
            messages=messages,
            tools=self.tools,
        )

    def _perform_api_call(self, api_kwargs: dict[str, Any]) -> Any:
        from agent.codex_runtime import create_response

        return create_response(self.client, api_kwargs)

    def _normalize_response(self, response: Any):
        return self.transport.normalize_response(response)

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
