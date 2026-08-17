"""Teaching time tool. Importing this module registers the tool."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
    try:
        timezone_info = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unknown IANA timezone: {timezone}") from exc
    current_time = datetime.now(timezone_info)
    return f"{timezone} 的时间是 {current_time:%Y-%m-%d %H:%M:%S}"


registry.register(
    name="get_current_time",
    toolset="time",
    schema=GET_CURRENT_TIME_SCHEMA,
    handler=_handle_get_current_time,
)
