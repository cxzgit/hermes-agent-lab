"""Public Agent object, matching run_agent.py's forwarding pattern."""

from __future__ import annotations

import os
from typing import Any

from agent.transports.codex import ResponsesApiTransport
from hermes_state import SessionDB
from model_tools import get_tool_definitions


class AIAgent:
    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key: str | None = None,
        client: Any = None,
        session_db: SessionDB | None = None,
        session_id: str | None = None,
        max_iterations: int = 10,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
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
        self._session_db = session_db
        self.session_id = session_id
        self.max_iterations = max_iterations

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

        history_size = len(conversation_history or [])
        result = run_conversation(
            self,
            user_message=user_message,
            conversation_history=conversation_history,
        )
        self._persist_session(result["messages"], history_size)
        return result

    def _persist_session(
        self,
        messages: list[dict[str, Any]],
        history_size: int,
    ) -> None:
        """Persist only the messages added by the current Agent turn."""
        if self._session_db is None or self.session_id is None:
            return
        pending_messages = messages[history_size:]
        inserted = self._session_db.append_messages_batch(
            self.session_id,
            pending_messages,
        )
        print(f"[10] persisted {inserted} new message(s) to SQLite")
