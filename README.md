# Mini Hermes：阶段一复现

这个项目复现 Hermes 第一阶段：读取命令行消息，把它转换成模型消息字典，
交给 Agent，并在多轮聊天中保留历史。

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
  -> fake_model()
```

`fake_model()` 代替真实模型 API，让你免费且稳定地观察数据流。阶段一不包含
工具、数据库、流式输出和复杂配置。

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

`pyproject.toml` 中仍然声明了 `mini-hermes = "hermes_cli.main:main"`，用于
学习真实项目的命令入口。等虚拟环境具备 setuptools 后，才需要尝试 editable
安装；阶段一运行和调试不依赖这一步。

## 断点顺序

1. `hermes_cli/main.py` 的 `main()`
2. `cli.py` 的 `HermesCLI.run()`
3. `cli.py` 的 `HermesCLI.chat()`
4. `run_agent.py` 的 `AIAgent.run_conversation()`
5. `agent/turn_context.py` 的 `build_turn_context()`
6. `agent/conversation_loop.py` 的 `fake_model()`

单步观察 `user_input`、`user_message`、`user_msg` 和 `messages`。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试验证：复制历史不会修改原列表，以及两轮聊天会复用历史。
