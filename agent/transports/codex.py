"""Minimal Responses API transport modeled after Hermes' codex transport."""

from __future__ import annotations

import json
from typing import Any

from agent.transports.types import NormalizedResponse, ToolCall, Usage


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


class ResponsesApiTransport:
    def convert_messages(
        self, messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for message in messages:
            role = message.get("role")
            if role == "system":
                continue
            if role == "tool":
                items.append(
                    {
                        "type": "function_call_output",
                        "call_id": message["tool_call_id"],
                        "output": str(message.get("content", "")),
                    }
                )
                continue

            content = message.get("content")
            if content:
                items.append({"role": role, "content": content})
            if role == "assistant":
                for tool_call in message.get("tool_calls", []):
                    arguments = tool_call.get("arguments", "{}")
                    if not isinstance(arguments, str):
                        arguments = json.dumps(arguments, ensure_ascii=False)
                    items.append(
                        {
                            "type": "function_call",
                            "call_id": tool_call["id"],
                            "name": tool_call["name"],
                            "arguments": arguments,
                        }
                    )
        return items

    def convert_tools(
        self, tools: list[dict[str, Any]] | None
    ) -> list[dict[str, Any]]:
        converted = []
        for tool in tools or []:
            function = tool["function"]
            converted.append(
                {
                    "type": "function",
                    "name": function["name"],
                    "description": function.get("description", ""),
                    "parameters": function.get(
                        "parameters", {"type": "object", "properties": {}}
                    ),
                }
            )
        return converted

    def build_kwargs(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        instructions = "You are Mini Hermes, a helpful assistant."
        payload_messages = messages
        if messages and messages[0].get("role") == "system":
            instructions = str(messages[0].get("content") or instructions)
            payload_messages = messages[1:]

        kwargs: dict[str, Any] = {
            "model": model,
            "instructions": instructions,
            "input": self.convert_messages(payload_messages),
            "store": False,
        }
        response_tools = self.convert_tools(tools)
        if response_tools:
            kwargs["tools"] = response_tools
            kwargs["tool_choice"] = "auto"
            kwargs["parallel_tool_calls"] = True
        return kwargs

    def normalize_response(self, response: Any) -> NormalizedResponse:
        content_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        for item in _value(response, "output", []) or []:
            item_type = _value(item, "type", "")
            if item_type == "message":
                for part in _value(item, "content", []) or []:
                    if _value(part, "type", "") in {"output_text", "text"}:
                        text = _value(part, "text", "")
                        if text:
                            content_parts.append(str(text))
            elif item_type in {"function_call", "custom_tool_call"}:
                call_id = _value(item, "call_id") or _value(item, "id")
                arguments = _value(item, "arguments", None)
                if arguments is None:
                    arguments = _value(item, "input", "{}")
                if not isinstance(arguments, str):
                    arguments = json.dumps(arguments, ensure_ascii=False)
                tool_calls.append(
                    ToolCall(
                        id=call_id,
                        name=str(_value(item, "name", "")),
                        arguments=arguments,
                        provider_data={"response_item_id": _value(item, "id")},
                    )
                )

        if not content_parts:
            output_text = _value(response, "output_text", "")
            if output_text:
                content_parts.append(str(output_text))

        raw_usage = _value(response, "usage")
        usage = None
        if raw_usage is not None:
            prompt_tokens = int(_value(raw_usage, "input_tokens", 0) or 0)
            completion_tokens = int(_value(raw_usage, "output_tokens", 0) or 0)
            usage = Usage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=int(
                    _value(
                        raw_usage,
                        "total_tokens",
                        prompt_tokens + completion_tokens,
                    )
                    or 0
                ),
            )

        status = str(_value(response, "status", "completed") or "completed")
        if tool_calls:
            finish_reason = "tool_calls"
        elif status == "incomplete":
            finish_reason = "incomplete"
        else:
            finish_reason = "stop"

        return NormalizedResponse(
            content="\n".join(content_parts).strip() or None,
            tool_calls=tool_calls or None,
            finish_reason=finish_reason,
            usage=usage,
        )
