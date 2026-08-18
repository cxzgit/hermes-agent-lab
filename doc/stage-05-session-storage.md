# 第五阶段：会话存储与恢复

这一阶段为 Mini Hermes 增加最小版 SQLite 会话持久化。

## 完整调用链

```text
首次启动
→ HermesCLI 创建 SessionDB
→ 生成 session_id
→ create_session()
→ AIAgent 完成一轮对话
→ _persist_session()
→ append_messages_batch()
→ BEGIN IMMEDIATE
→ 写入 messages
→ COMMIT

恢复启动
→ mini-hermes --resume <session_id>
→ SessionDB.session_exists()
→ get_messages_as_conversation()
→ ORDER BY id
→ conversation_history
→ 继续对话
```

## 表的职责

- `sessions`：保存会话身份、创建时间和消息总数。
- `messages`：保存 user、assistant、tool 消息以及工具调用信息。

`messages.session_id` 是指向 `sessions.id` 的外键。复杂的
`tool_calls` 使用 JSON 文本存储，恢复时再通过 `json.loads()` 还原。

## 原子批量写入

一轮工具对话可能产生 user、assistant tool call、tool result 和最终
assistant 四条消息。它们在同一个事务中写入：全部成功时提交，任意
一条失败时全部回滚。

## 与真实 Hermes 的差异

Mini 版本保留了最重要的学习结构，但没有复制 WAL/FTS5、压缩祖先链、
软删除、并发抖动重试、提示词缓存 sidecar 和多 Provider 推理字段。

## 运行

首次启动时终端会显示 session ID。退出后使用它恢复：

```powershell
mini-hermes --resume <session_id>
```
