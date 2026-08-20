"""Thin orchestration layer over the central tool registry."""

from __future__ import annotations

from typing import Any

from tools.registry import registry


def discover_builtin_tools() -> None:
    # Importing a tool module triggers its module-level registry.register().
    import tools.file_tools  # noqa: F401
    import tools.skills_tool  # noqa: F401
    import tools.time_tool  # noqa: F401
    # Plugins extend the registry through a controlled PluginContext.
    from hermes_cli.plugins import discover_plugins

    discover_plugins()


discover_builtin_tools()


def get_tool_definitions() -> list[dict[str, Any]]:
    return registry.get_definitions()


def handle_function_call(function_name: str, function_args: dict[str, Any]) -> str:
    return registry.dispatch(function_name, function_args)
