"""Central registry for Mini Hermes tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


ToolHandler = Callable[[dict[str, Any]], str]


@dataclass(frozen=True)
class ToolEntry:
    name: str
    toolset: str
    schema: dict[str, Any]
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolEntry] = {}

    def register(
        self,
        *,
        name: str,
        toolset: str,
        schema: dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")
        self._tools[name] = ToolEntry(name, toolset, schema, handler)

    def get_definitions(self) -> list[dict[str, Any]]:
        """Return schemas in the format sent to a model API."""
        return [
            {
                "type": "function",
                "function": {**entry.schema, "name": entry.name},
            }
            for entry in self._tools.values()
        ]

    def dispatch(self, name: str, args: dict[str, Any]) -> str:
        """Look up a tool by name and execute its handler."""
        entry = self._tools.get(name)
        if entry is None:
            return f"Unknown tool: {name}"
        try:
            return entry.handler(args)
        except Exception as exc:
            return f"Tool execution failed: {type(exc).__name__}: {exc}"


registry = ToolRegistry()

