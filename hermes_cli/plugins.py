"""Small runtime plugin loader used by Mini Hermes.

The real project has a much larger manager.  This version keeps the same
important seam: ``plugin.yaml`` is metadata, while ``register(ctx)`` is the
only code entry point and the context owns registrations.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

from tools.registry import registry


@dataclass(frozen=True)
class PluginManifest:
    name: str
    version: str = ""
    description: str = ""
    path: Path | None = None
    hooks: list[str] = field(default_factory=list)


class PluginContext:
    """Controlled facade passed to a plugin's ``register(ctx)`` function."""

    def __init__(self, manifest: PluginManifest, manager: "PluginManager") -> None:
        self.manifest = manifest
        self._manager = manager

    @property
    def plugin_id(self) -> str:
        return self.manifest.name

    def register_tool(
        self,
        *,
        name: str,
        schema: dict[str, Any],
        handler: Callable[[dict[str, Any]], str],
        toolset: str = "plugin",
    ) -> None:
        registry.register(
            name=name,
            toolset=toolset,
            schema=schema,
            handler=handler,
        )
        self._manager._registered_tools.setdefault(self.plugin_id, []).append(name)

    def register_hook(self, name: str, callback: Callable[..., Any]) -> None:
        self._manager._hooks.setdefault(name, []).append(callback)


class PluginManager:
    def __init__(self, plugins_dir: Path | str | None = None) -> None:
        self.plugins_dir = Path(plugins_dir or Path(__file__).resolve().parents[1] / "plugins")
        self._discovered = False
        self._plugins: dict[str, PluginManifest] = {}
        self._hooks: dict[str, list[Callable[..., Any]]] = {}
        self._registered_tools: dict[str, list[str]] = {}

    @property
    def plugins(self) -> dict[str, PluginManifest]:
        return dict(self._plugins)

    def discover_and_load(self, *, force: bool = False) -> None:
        if self._discovered and not force:
            return
        self._discovered = True
        if not self.plugins_dir.is_dir():
            return
        for plugin_dir in sorted(self.plugins_dir.iterdir()):
            manifest_file = plugin_dir / "plugin.yaml"
            init_file = plugin_dir / "__init__.py"
            if not plugin_dir.is_dir() or not manifest_file.is_file() or not init_file.is_file():
                continue
            data = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
            name = str(data.get("name") or plugin_dir.name)
            manifest = PluginManifest(
                name=name,
                version=str(data.get("version") or ""),
                description=str(data.get("description") or ""),
                path=plugin_dir,
                hooks=list(data.get("hooks") or []),
            )
            module_name = f"mini_hermes_plugin_{name.replace('-', '_')}"
            spec = importlib.util.spec_from_file_location(module_name, init_file)
            if spec is None or spec.loader is None:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            register = getattr(module, "register", None)
            if not callable(register):
                continue
            self._plugins[name] = manifest
            register(PluginContext(manifest, self))

    def invoke_hook(self, name: str, **kwargs: Any) -> list[Any]:
        return [callback(**kwargs) for callback in self._hooks.get(name, [])]


_manager: PluginManager | None = None


def get_plugin_manager() -> PluginManager:
    global _manager
    if _manager is None:
        _manager = PluginManager()
    return _manager


def discover_plugins(*, force: bool = False) -> PluginManager:
    manager = get_plugin_manager()
    manager.discover_and_load(force=force)
    return manager
