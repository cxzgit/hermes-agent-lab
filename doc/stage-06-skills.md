# 第六阶段：Skill 加载与执行

## 学习目标

这一阶段复现 Hermes Agent 的最小 Skill 主链：启动时只扫描 Skill 元数据，
用户明确调用时才完整读取 `SKILL.md`，然后把 Skill 指令作为普通 `user`
消息送入现有 Agent Loop。

## 完整调用链

```text
Mini Hermes 启动
→ HermesCLI.__init__()
→ scan_skill_commands()
→ 递归寻找 skills/**/SKILL.md
→ parse_frontmatter()
→ 建立 /command → Skill 元数据索引

用户输入 /explain-code 解释 SQLite 事务
→ HermesCLI.prepare_user_input()
→ build_skill_invocation_message()
→ skill_view()
→ 验证 Skill 路径
→ 完整读取 SKILL.md
→ 列出 references/templates/scripts/assets
→ 拼接 activation note、Skill 正文和用户任务
→ HermesCLI.chat(expanded_message)
→ AIAgent.run_conversation()
→ build_turn_context()
→ {"role": "user", "content": "完整 Skill 调用消息"}
→ 模型调用 read_file 读取项目源码，或调用 skill_view 读取 Skill 支持文件
→ SQLite 保存本轮历史
```

## 文件职责

| 文件 | 职责 |
|---|---|
| `agent/skill_commands.py` | 解析 Frontmatter、扫描命令索引、构造 Skill 调用消息 |
| `tools/skills_tool.py` | 安全读取主 Skill 或支持文件，并注册 `skill_view` 工具 |
| `tools/file_tools.py` | 完整读取项目内文本文件，并阻止路径逃逸 |
| `cli.py` | 在聊天前把 `/skill-name` 展开为普通用户输入 |
| `skills/learning/explain-code/SKILL.md` | 示例 Skill 的完整工作说明 |
| `tests/test_stage_six.py` | 验证扫描、路径安全、消息构造和 CLI 集成 |

## 轻量索引与按需加载

`scan_skill_commands()` 只保存：

```python
{
    "/explain-code": {
        "name": "explain-code",
        "description": "...",
        "identifier": "learning/explain-code",
        "skill_md_path": ".../SKILL.md",
        "skill_dir": ".../explain-code",
    }
}
```

索引中没有完整正文。只有用户调用 `/explain-code` 或模型调用
`skill_view` 时，程序才读取 `SKILL.md`。

## 为什么作为 user 消息

Skill 是用户本轮明确选择的工作流程。它不修改 system prompt，而是和用户的
具体任务一起成为新的 `user` 消息，从而复用现有 Agent Loop、工具调用、历史
记录和 SQLite 持久化，同时保持对话的 system prompt 稳定。

## 路径安全

`skill_view()` 拒绝绝对路径和包含 `..` 的路径，并在解析后再次验证目标仍位于
Skill 目录中。这可以防止通过 `file_path` 读取 Skill 目录之外的文件。

`read_file()` 使用相同的双层边界检查，但范围是 Mini Hermes 项目根目录。
它支持 `agent/skill_commands.py` 这样的精确相对路径；只有文件名在项目中唯一时，
才允许使用 `skill_commands.py` 这样的裸文件名。它完整读取文件，不提供会诱导模型
只读一部分内容的分页参数。

## 与真实 Hermes 的区别

Mini 版本保留学习主链，没有复现：

- profile 级 `HERMES_HOME/skills` 与外部目录缓存；
- 插件和组织共享 Skill；
- 平台、运行环境和 disabled 配置过滤；
- 环境变量与凭据文件的交互式配置；
- Skill Bundle、Stacked Skill 和预加载；
- Inline Shell、模板变量及 Prompt Cache 稳定边界；
- 使用统计和重复读取指纹。

## 手动验证

```powershell
mini-hermes
```

输入：

```text
/explain-code 请解释 hermes_state.py 中的 _execute_write
```

观察输出中的：

```text
[skill] loaded: explain-code
```

然后在 `HermesCLI.chat()` 或 `build_turn_context()` 设置断点，确认发送给模型的
是一条包含完整 Skill 正文和用户任务的 `role=user` 消息。
