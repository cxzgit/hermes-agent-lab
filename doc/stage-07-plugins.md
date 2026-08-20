# 第七阶段：Plugin 扩展机制

Mini Hermes 复现了真实 Hermes 的最小插件链路：

```text
model_tools.discover_builtin_tools()
  -> discover_plugins()
  -> PluginManager.discover_and_load()
  -> plugins/<name>/plugin.yaml
  -> plugins/<name>/__init__.py
  -> register(PluginContext)
  -> ctx.register_tool()
  -> tools.registry
  -> AIAgent.tools
```

`plugin.yaml` 只描述插件元数据；真正的执行入口是 `register(ctx)`。插件不直接
修改 Agent，而是通过 `PluginContext` 注册工具或 Hook。这样宿主仍然掌握注册表，
后续才有机会实现启用、禁用和卸载。

示例插件位于 `plugins/demo/`，注册 `plugin_repeat`。可以在测试中验证：

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_stage_seven -v
```

推荐断点：`hermes_cli/plugins.py` 的 `discover_and_load()`、插件的
`register(ctx)`，以及 `tools/registry.py` 的 `register()`。
