"""Teaching time tool. Importing this module registers the tool."""

from __future__ import annotations

from typing import Any

from tools.registry import registry


GET_CURRENT_TIME_SCHEMA = {
    "description": "Get the current time for an IANA timezone.",
    "parameters": {
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "IANA timezone such as Asia/Shanghai.",
            }
        },
        "required": ["timezone"],
        "additionalProperties": False,
    },
}


def _handle_get_current_time(args: dict[str, Any]) -> str:
    timezone = args["timezone"]
    # Fixed output keeps tests deterministic. A later exercise can use
    # datetime/zoneinfo without changing the registry or Agent loop.
    return f"{timezone} 的时间是 2026-08-13 10:00:00"


registry.register(
    name="get_current_time",
    toolset="time",
    schema=GET_CURRENT_TIME_SCHEMA,
    handler=_handle_get_current_time,
)

