# Mini Hermes 学习文档

这里记录 Hermes Agent 的分阶段学习与复现结果。

## 阶段目录

| 阶段 | 内容 | 状态 | 文档 |
|---|---|---|---|
| 第一阶段 | CLI 输入到 Agent 消息 | 已完成 | [stage-01-cli-message-flow.md](stage-01-cli-message-flow.md) |
| 第二阶段 | 模型响应与 Agent 循环 | 已完成 | [stage-02-agent-loop.md](stage-02-agent-loop.md) |
| 第三阶段 | 工具注册、调用与结果回传 | 已完成 | [stage-03-tool-system.md](stage-03-tool-system.md) |
| 第四阶段 | Responses API 与真实模型 Provider | 已完成 | [stage-04-real-model-provider.md](stage-04-real-model-provider.md) |
| 第五阶段 | 会话存储与恢复 | 已完成 | [stage-05-session-storage.md](stage-05-session-storage.md) |
| 第六阶段 | Skill 加载与执行 | 已完成 | [stage-06-skills.md](stage-06-skills.md) |
| 第七阶段 | Plugin 扩展机制 | 未开始 | 待创建 |

## 总体学习路线

```text
CLI
→ Agent 循环
→ 工具系统
→ 真实模型
→ 会话存储
→ Skill
→ Plugin
```
