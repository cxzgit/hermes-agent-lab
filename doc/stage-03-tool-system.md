# 第三阶段：工具注册、暴露与执行

## 阶段目标

理解工具为什么不应该写死在 Agent 循环中，以及 Hermes 如何用中央注册表把工具的
Schema 和 Handler 连接起来。

## 第三阶段的完整调用链

```text
注册工具
tools/time_tool.py
→ registry.register(name, schema, handler)
→ ToolRegistry 保存 ToolEntry

告诉模型
registry.get_definitions()
→ model_tools.get_tool_definitions()
→ agent.tools
→ 模型请求的 tools 参数

执行工具
模型返回 tool_calls
→ agent/tool_executor.py
→ model_tools.handle_function_call(name, args)
→ registry.dispatch(name, args)
→ 找到 ToolEntry.handler
→ 执行 _handle_get_current_time(args)
→ 构造 Tool 消息
→ Agent 循环 continue
```

## Mini 项目各文件的职责

| 文件 | 职责 |
|---|---|
| `tools/registry.py` | 保存工具条目、输出 Schema、按名称分发 Handler |
| `tools/time_tool.py` | 定义时间工具的 Schema、Handler 并完成注册 |
| `model_tools.py` | 工具系统的薄编排层，负责发现、Schema 查询和调用分发 |
| `agent/tool_executor.py` | 解析模型参数、调用工具并构造 Tool 消息 |
| `agent/conversation_loop.py` | 只负责 Agent 控制流，不再认识具体工具实现 |
| `run_agent.py` | 初始化 `agent.tools` 和 `valid_tool_names` |
| `tests/test_stage_three.py` | 验证 Schema 暴露、Handler 分发及错误行为 |

## Schema 与 Handler

一个工具同时注册两类信息：

```python
registry.register(
    name="get_current_time",
    toolset="time",
    schema=GET_CURRENT_TIME_SCHEMA,
    handler=_handle_get_current_time,
)
```

```text
Schema   给模型看的使用说明书
Handler  本地真正执行工作的 Python 函数
```

模型不会读取 Handler 的源码；本地程序也不会让模型直接执行任意 Python 函数。

## 为什么使用注册表

写死条件判断会让 Agent 循环依赖每一个具体工具：

```python
if name == "get_current_time":
    ...
elif name == "read_file":
    ...
```

注册表把它改为统一分发：

```python
entry = registry.get_entry(name)
return entry.handler(args)
```

因此添加工具时无需修改 Agent 循环。

## 模块导入即注册

`model_tools.discover_builtin_tools()` 导入 `tools.time_tool`。模块顶层的
`registry.register()` 在导入时执行，因此工具进入全局注册表。这与真实 Hermes
工具模块的自注册方式一致。

## Tool 消息协议

工具执行器产生：

```python
{
    "role": "tool",
    "name": "get_current_time",
    "tool_call_id": "call_get_current_time_1",
    "content": "Asia/Shanghai 的时间是 2026-08-13 10:00:00",
}
```

`tool_call_id` 必须对应前一条 Assistant 工具请求的 ID。

## 测试

```powershell
python -m unittest discover -s tests -v
```

## 阶段验收

完成第三阶段后，应当能够解释：

1. Schema 与 Handler 的区别。
2. 工具模块为什么在导入时调用 `registry.register()`。
3. `get_tool_definitions()` 如何让模型知道工具存在。
4. `registry.dispatch()` 如何根据名称找到 Handler。
5. 为什么新增工具不应该修改 `conversation_loop.py`。

