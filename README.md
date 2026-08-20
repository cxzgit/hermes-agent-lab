# Mini Hermes：分阶段复现 Hermes Agent

这是一个用于学习 [Hermes Agent](https://github.com/NousResearch/hermes-agent)
核心工作原理的精简实现。项目按照真实 Hermes Agent 的主要目录和调用关系，
逐阶段复现 CLI、Agent Loop、工具调用、OpenAI Responses API、基于 SQLite
的会话持久化与恢复，以及 Skill 的按需加载。

它不是 Hermes Agent 的替代品，而是一个可以单步调试、阅读和修改的学习项目。

## 已完成阶段

1. CLI 命令入口与用户输入调用链
2. Agent 循环与多轮工具调用
3. 工具注册、Schema 生成与工具执行
4. 真实 OpenAI Responses API 与响应标准化
5. SQLite 会话存储、事务写入与 `--resume` 恢复
6. Skill 扫描、安全读取与 Slash Command 调用
7. Plugin manifest、`register(ctx)` 与插件工具注册

## 调用链

```text
pyproject.toml: mini-hermes
  -> hermes_cli.main:main()
  -> cmd_chat()
  -> cli.main()
  -> HermesCLI.run()
  -> HermesCLI.chat(user_input)
  -> AIAgent.run_conversation()
  -> agent.conversation_loop.run_conversation()
  -> build_turn_context()
  -> {"role": "user", "content": "..."}
  -> ResponsesApiTransport
  -> OpenAI Responses Client
  -> NormalizedResponse
  -> AIAgent._persist_session()
  -> SessionDB.append_messages_batch()
  -> .mini-hermes/state.db
```

Skill 调用复用同一条聊天链：

```text
/explain-code <任务>
  -> scan_skill_commands()
  -> build_skill_invocation_message()
  -> skill_view()
  -> 完整 SKILL.md + 用户任务
  -> HermesCLI.chat()
  -> {"role": "user", "content": "..."}
  -> read_file() 按需读取项目源码
```

单元测试通过注入 Mock Client 保持免费、稳定；正常运行只使用真实 OpenAI
Client，不保留 Fake Model 运行模式。

## 安装

```powershell
cd E:\Learning\github-lab\hermes-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

项目新增顶层模块、依赖、命令入口或修改 `pyproject.toml` 后，应重新执行：

```powershell
python -m pip install -e .
```

## 配置

复制环境变量示例文件：

```powershell
Copy-Item .env.example .env
```

在 `.env` 中填写密钥：

```dotenv
OPENAI_API_KEY=你的_API_Key
```

模型名和 API 地址保存在 `config.yaml`。`.env` 只保存密钥，`.env.example`
只作示例，不会被程序读取。

## 运行

```powershell
cd E:\Learning\github-lab\hermes-agent
.\.venv\Scripts\Activate.ps1
mini-hermes
```

输入两条消息，然后输入 `/quit`。也可以直接运行包入口：

```powershell
python -m hermes_cli.main
```

启动时会显示当前 `session_id`。退出后可以恢复原会话：

```powershell
mini-hermes --resume <session_id>
```

调用内置示例 Skill：

```text
/explain-code 请解释 hermes_state.py 中的事务代码
```

数据库默认保存在：

```text
.mini-hermes/state.db
```

`pyproject.toml` 声明了 `mini-hermes = "hermes_cli.main:main"`，因此命令最终
进入 `hermes_cli.main:main()`。数据库和 `.env` 均已被 Git 忽略。

## 推荐断点顺序

1. `hermes_cli/main.py` 的 `main()`
2. `cli.py` 的 `HermesCLI.run()`
3. `cli.py` 的 `HermesCLI.chat()`
4. `run_agent.py` 的 `AIAgent.run_conversation()`
5. `agent/turn_context.py` 的 `build_turn_context()`
6. `agent/conversation_loop.py` 的 `run_conversation()`
7. `run_agent.py` 的 `_perform_api_call()`
8. `agent/transports/codex.py` 的 `build_kwargs()` 与 `normalize_response()`
9. `tools/registry.py` 的 `dispatch()`
10. `hermes_state.py` 的 `append_messages_batch()`
11. `hermes_state.py` 的 `_execute_write()`
12. `hermes_state.py` 的 `get_messages_as_conversation()`

单步观察 `user_input`、`messages`、`tool_calls`、`history_size`、`session_id`
以及数据库事务的 `commit()` / `rollback()`。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试验证：历史复制、Agent Loop、工具系统、真实 Responses API 请求结构、
SQLite 批量事务回滚、会话恢复、Skill 扫描、路径安全和 Skill 用户消息注入。

当前向模型暴露内置工具以及示例插件工具 `plugin_repeat`；插件工具通过
`plugin.yaml` 和 `register(ctx)` 加载，最终进入同一个工具注册表。
`read_file` 只能完整读取 Mini Hermes 项目目录中的 UTF-8 文本文件。

一次用户回合默认最多调用模型 `10` 轮，由 `AIAgent.max_iterations` 控制；
它限制的是 API 迭代轮数，不是工具数量。

## 学习文档

每个阶段的调用链、文件职责和复现重点位于 [`doc/`](doc/) 目录。

## 与真实 Hermes Agent 的区别

Mini Hermes 只保留理解主调用链所需的代码。真实 Hermes Agent 还包含多 Provider、
WAL 与 FTS5、并发写入重试、上下文压缩、Skills、Plugins、Gateway、TUI、Desktop
和多种终端后端等生产级能力。
