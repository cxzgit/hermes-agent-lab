# 第一阶段：CLI 输入到 Agent 消息

## 阶段目标

理解一条用户消息如何从 PowerShell 进入程序，经过 CLI 和 Agent，转换成模型使用的
消息结构，得到回答后保存到对话历史并显示在终端。

本阶段重点是程序的数据流和模块职责，不涉及真实模型 API、工具调用、数据库、
流式输出、Memory、Skill 或 Plugin。

## 第一阶段的完整调用链

需要掌握的核心地图：

```text
PowerShell 输入 mini-hermes
→ pyproject.toml 找到命令入口
→ hermes_cli.main:main()
→ cmd_chat()
→ cli.main()
→ 创建 HermesCLI
→ HermesCLI.run() 读取输入
→ HermesCLI.chat(user_input)
→ AIAgent.run_conversation()
→ conversation_loop.run_conversation()
→ build_turn_context()
→ 构造 {"role": "user", "content": "..."}
→ 加入 messages
→ 调用模型（mini 项目中为 fake_model）
→ 加入 assistant 消息
→ 保存历史
→ CLI 显示回答
```

## 真实 Hermes 与 Mini 项目的对应关系

| 环节 | 真实 Hermes | Mini 项目 |
|---|---|---|
| 命令入口 | `hermes = "hermes_cli.main:main"` | `mini-hermes = "hermes_cli.main:main"` |
| 命令分发 | `hermes_cli/main.py` | `hermes_cli/main.py` |
| 经典 CLI | `cli.py` | `cli.py` |
| Agent 公共入口 | `run_agent.AIAgent` | `run_agent.AIAgent` |
| 对话循环 | `agent/conversation_loop.py` | `agent/conversation_loop.py` |
| 本轮上下文 | `agent/turn_context.py` | `agent/turn_context.py` |
| 模型调用 | 多 Provider 传输层 | `fake_model()` |

## Mini 项目各文件的职责

| 文件 | 职责 |
|---|---|
| `pyproject.toml` | 声明 `mini-hermes` 命令入口 |
| `hermes_cli/main.py` | 解析命令并进入聊天 |
| `cli.py` | 读取输入、显示回答、保存历史 |
| `run_agent.py` | 提供 `AIAgent` 公共入口 |
| `agent/turn_context.py` | 把输入转换成消息字典 |
| `agent/conversation_loop.py` | 组织一次对话并调用假模型 |
| `tests/test_stage_one.py` | 验证历史复制和多轮聊天 |

## 核心数据变化

用户在 PowerShell 中输入的是裸字符串：

```python
"你好"
```

`build_turn_context()` 将它转换为带角色的消息：

```python
{"role": "user", "content": "你好"}
```

模型回答后，消息列表变为：

```python
[
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "我收到了：你好"},
]
```

第二轮输入会追加在历史后面，而不是丢弃第一轮：

```python
[
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "我收到了：你好"},
    {"role": "user", "content": "第二轮"},
]
```

因此模型能够理解上下文的基础是：每次请求时，把相关对话历史一起传入。

## 为什么复制历史列表

代码使用：

```python
messages = list(conversation_history) if conversation_history else []
```

这样 `messages.append(...)` 不会直接修改调用者传入的外层列表。这里是浅复制：
新建了列表，但列表内已有的字典仍然是原来的对象。

## 模块职责

### 命令层

`pyproject.toml` 和 `hermes_cli/main.py` 负责回答：用户执行哪个命令，程序应进入哪个功能。

### CLI 层

`cli.py` 负责读取终端输入、调用 Agent、保存返回的历史并显示回答。

### Agent 公共入口

`run_agent.py` 提供稳定的 `AIAgent.run_conversation()` 方法，再将具体工作转发给专门的对话循环模块。

### 对话循环

`agent/conversation_loop.py` 负责组织一次对话：准备消息、调用模型、加入 Assistant 回答并返回结果。

### 本轮上下文

`agent/turn_context.py` 负责把裸输入转换成标准消息字典，并与历史消息组合。

## 如何运行复现项目

```powershell
cd E:\Learning\github-lab\hermes-agent
.\.venv\Scripts\Activate.ps1
mini-hermes
```

输入两条消息，然后输入：

```text
/quit
```

第二轮应看到类似日志：

```text
[6] conversation_loop sends 3 message(s) to fake_model
```

这三条消息是第一轮 User、第一轮 Assistant 和第二轮 User。

## 如何运行测试

```powershell
python -m unittest discover -s tests -v
```

测试验证两个行为：

1. `build_turn_context()` 不直接修改调用者传入的历史列表。
2. `HermesCLI` 在两轮聊天之间保留并复用消息历史。

## 建议断点顺序

1. `hermes_cli/main.py` 的 `main()`
2. `cli.py` 的 `HermesCLI.run()`
3. `cli.py` 的 `HermesCLI.chat()`
4. `run_agent.py` 的 `AIAgent.run_conversation()`
5. `agent/turn_context.py` 的 `build_turn_context()`
6. `agent/conversation_loop.py` 的 `fake_model()`

单步观察以下变量：

```text
user_input
→ message
→ user_message
→ user_msg
→ messages 中的一项
```

## 阶段验收

完成第一阶段后，应当能够解释：

1. `mini-hermes` 命令为什么会调用 `hermes_cli.main:main()`。
2. `HermesCLI.run()` 和 `HermesCLI.chat()` 的职责有什么区别。
3. 用户字符串如何变成 `{"role": "user", "content": "..."}`。
4. 为什么第二轮模型请求中包含第一轮消息。
5. 为什么 Agent 的公开入口和对话循环实现分布在不同文件中。

