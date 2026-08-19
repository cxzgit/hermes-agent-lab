# 第二阶段：模型响应与 Agent 循环

## 阶段目标

理解 Hermes 收到模型响应后，如何根据 `tool_calls` 选择两条路径：直接结束，
或者执行工具并再次调用模型。

## 第二阶段的完整调用链

```text
messages
→ 调用模型
→ normalize_response(response)
→ assistant_message
→ 检查 assistant_message.tool_calls
   ├─ 无工具调用
   │  → final_response = assistant_message.content
   │  → 加入 Assistant 消息
   │  → break 退出循环
   │  → finalize_turn() 返回结果
   └─ 有工具调用
      → 加入带 tool_calls 的 Assistant 消息
      → 执行工具
      → 加入带 tool_call_id 的 Tool 消息
      → continue 回到循环开头
      → 再次调用模型
      → 模型根据工具结果生成最终文本
```

## Mini 项目各文件的职责

| 文件 | 第二阶段职责 |
|---|---|
| `agent/conversation_loop.py` | 实现有次数限制的 Agent 循环和两条响应分支 |
| 测试 Mock Client | 在单元测试中提供标准化前的 Responses 响应，不进入运行时代码 |
| `execute_tool_call()` | 临时执行教学工具；第三阶段会替换成工具注册系统 |
| `tests/test_stage_two.py` | 验证普通响应只调用模型一次，工具响应会调用两次 |

## 普通回答路径

输入普通消息时，假模型返回：

```python
{
    "content": "我收到了：hello",
    "tool_calls": [],
    "finish_reason": "stop",
}
```

因为 `tool_calls` 为空，循环保存 Assistant 回答并执行 `break`。

## 工具调用路径

输入“现在几点？”时，第一次模型响应包含：

```python
{
    "content": "我先查询时间。",
    "tool_calls": [
        {
            "id": "call_get_current_time_1",
            "name": "get_current_time",
            "arguments": "{...}",
        }
    ],
    "finish_reason": "tool_calls",
}
```

程序先保存 Assistant 工具请求，再执行工具并保存结果：

```python
{
    "role": "tool",
    "name": "get_current_time",
    "tool_call_id": "call_get_current_time_1",
    "content": "Asia/Shanghai 的时间是 2026-08-13 10:00:00",
}
```

`tool_call_id` 必须与 Assistant 请求中的 `id` 相同，建立请求和结果的对应关系。

执行 `continue` 后，第二次模型调用看到完整顺序：

```text
User
→ Assistant(tool_calls)
→ Tool(tool_call_id, content)
```

于是生成最后一条普通 Assistant 回答，并通过 `break` 结束循环。

## break 与 continue

```text
break     最终回答已经产生，退出 Agent 循环
continue  工具结果已经产生，回到循环开头再次调用模型
```

这是第二阶段最重要的控制流区别。

## 最大迭代次数

Mini Hermes 通过 `AIAgent.max_iterations` 控制一次用户回合最多调用模型多少轮，
默认值为 `10`：

```python
while api_call_count < agent.max_iterations:
```

这个数值不是工具数量。一轮模型响应可以并行请求多个工具，但只增加一次
`api_call_count`。真实 Hermes 当前默认值为 `90`，并额外受到共享迭代预算、
中断和 grace call 控制；Mini 使用较小默认值以限制学习时的 API 消耗。

## 运行观察

```powershell
mini-hermes
```

先输入：

```text
你好
```

应看到模型只被调用一次。再输入：

```text
现在几点？
```

应看到工具路径以及第二次循环。

## 测试

```powershell
python -m unittest discover -s tests -v
```

## 阶段验收

完成第二阶段后，应当能够解释：

1. 为什么 Provider 响应需要先标准化。
2. `assistant_message.tool_calls` 如何决定控制流。
3. 为什么工具结果前必须存在 Assistant 工具请求。
4. `tool_call_id` 有什么作用。
5. 工具执行后为什么使用 `continue`，最终文本后为什么使用 `break`。
