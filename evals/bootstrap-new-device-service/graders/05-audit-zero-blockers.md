---
type: llm
focus: trace
weight: 1
---

对 fan-controller 运行 audit_project.py（等级 2）结果 blocker 为 0；本机没有 cargo 时允许只剩 B-LOCK（Cargo.lock 需要工具链才能生成），但不允许伪造锁文件
