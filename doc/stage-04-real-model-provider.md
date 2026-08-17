# 第四阶段：真实模型 Provider

## 学习目标

把前三阶段已经完成的消息、Agent Loop 和工具系统接到真实 OpenAI
Responses API。运行时只使用 OpenAI Client，离线测试使用测试内 Mock。

## 完整调用链

```text
mini-hermes
→ config.yaml 读取 model、base_url
→ .env 读取 OPENAI_API_KEY
→ HermesCLI 创建 AIAgent(provider="openai")
→ ResponsesApiTransport.build_kwargs()
→ system 消息提取为 instructions
→ 其他消息转换为 input items
→ 工具 schema 转换为 Responses function 定义
→ codex_runtime.create_response()
→ client.responses.create(**api_kwargs)
→ ResponsesApiTransport.normalize_response()
→ NormalizedResponse
→ conversation_loop 判断 tool_calls 或最终文本
```

## 文件职责

| 文件 | 职责 |
|---|---|
| `hermes_cli/config.py` | 从 `.env` 加载密钥，从 `config.yaml` 加载模型设置 |
| `run_agent.py` | 创建 OpenAI Client，公开请求、调用与标准化方法 |
| `agent/transports/types.py` | 定义统一的 `ToolCall`、`Usage`、`NormalizedResponse` |
| `agent/transports/codex.py` | 构造 Responses 请求并标准化响应 |
| `agent/codex_runtime.py` | 真正执行 `client.responses.create()` |
| `agent/conversation_loop.py` | 只依赖统一响应，不依赖具体 Provider |
| `tests/test_stage_four.py` | 验证请求转换、工具配对和 API 调用边界 |

## 请求转换

内部消息：

```python
[
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "hello"},
]
```

Responses 请求：

```python
{
    "model": "gpt-5.2",
    "instructions": "You are helpful.",
    "input": [{"role": "user", "content": "hello"}],
    "store": False,
}
```

工具请求和工具结果分别变成 `function_call` 与
`function_call_output`，二者使用相同 `call_id` 配对。

## 为什么需要 NormalizedResponse

Provider 的原始响应格式不同。Transport 把它们统一成：

```python
NormalizedResponse(
    content="...",
    tool_calls=[...],
    finish_reason="stop"或"tool_calls",
)
```

这样 Agent Loop 无需知道底层使用 Responses、Chat Completions、Anthropic
还是其他协议。

## 安装和运行

安装 OpenAI 可选依赖：

```powershell
pip install -e .
```

把 `.env.example` 复制为 `.env`，只填写密钥：

```powershell
Copy-Item .env.example .env
```

```dotenv
OPENAI_API_KEY=你的 API Key
```

在 `config.yaml` 中配置非秘密设置：

```yaml
model:
  name: gpt-5.2
  base_url: https://api.openai.com/v1
```

然后直接运行：

```powershell
mini-hermes
```

不要把 API Key 写进源码、`config.yaml` 或提交到 Git。模型和地址只从
`config.yaml` 读取，不提供命令行覆盖。
