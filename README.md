# Mini Hermes：分阶段复现

这个项目分阶段复现 Hermes Agent 的 CLI、Agent Loop、工具系统、真实 OpenAI
Responses API，以及基于 SQLite 的会话存储与恢复。

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

单元测试通过注入 Mock Client 保持免费、稳定；运行时只保留真实 OpenAI Client。

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

`pyproject.toml` 中仍然声明了 `mini-hermes = "hermes_cli.main:main"`，用于
学习真实项目的命令入口。等虚拟环境具备 setuptools 后，才需要尝试 editable
安装；阶段一运行和调试不依赖这一步。

## 断点顺序

1. `hermes_cli/main.py` 的 `main()`
2. `cli.py` 的 `HermesCLI.run()`
3. `cli.py` 的 `HermesCLI.chat()`
4. `run_agent.py` 的 `AIAgent.run_conversation()`
5. `agent/turn_context.py` 的 `build_turn_context()`
6. `run_agent.py` 的 `_perform_api_call()`

单步观察 `user_input`、`user_message`、`user_msg` 和 `messages`。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试验证：历史复制、Agent Loop、工具系统、真实 Responses API 请求结构、
SQLite 批量事务回滚，以及重新创建 CLI 后恢复原会话。
