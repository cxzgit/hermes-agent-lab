# Mini Hermes 学习文档

这里记录 Hermes Agent 的分阶段学习与复现结果。

学习原则：每完成一个阶段，先梳理真实 Hermes 的调用链，再在 mini 项目中复现，
最后记录完整调用链、文件职责、关键概念和验收方式。

## 阶段目录

| 阶段 | 内容 | 状态 | 文档 |
|---|---|---|---|
| 第一阶段 | CLI 输入到 Agent 消息 | 已完成 | [stage-01-cli-message-flow.md](stage-01-cli-message-flow.md) |
| 第二阶段 | 模型响应与 Agent 循环 | 已完成 | [stage-02-agent-loop.md](stage-02-agent-loop.md) |
| 第三阶段 | 工具注册、调用与结果回传 | 未开始 | 待创建 |
| 第四阶段 | 会话存储与恢复 | 未开始 | 待创建 |
| 第五阶段 | Skill 加载与执行 | 未开始 | 待创建 |
| 第六阶段 | Plugin 扩展机制 | 未开始 | 待创建 |

## 总体学习路线

```text
CLI
→ Agent 循环
→ 工具系统
→ 会话存储
→ Skill
→ Plugin
```

