"""Small canonical response types shared by every provider transport."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolCall:
    id: str | None
    name: str
    arguments: str
    provider_data: dict[str, Any] | None = None


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class NormalizedResponse:
    content: str | None
    tool_calls: list[ToolCall] | None
    finish_reason: str
    reasoning: str | None = None
    usage: Usage | None = None
    provider_data: dict[str, Any] | None = None
