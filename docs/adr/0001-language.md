# ADR-0001：主语言选择

- 状态：已接受
- 日期：2026-11-02

## 背景
本仓库的内容是给 AI 读的 Markdown；脚本要在任何构建机上零安装就能跑。

## 候选方案
1. Python 3.11+ 标准库：到处都有，`tomllib` 读预算文件，不加依赖。
2. Rust / Go：性能无意义，还要编译。
3. 纯 bash：复杂的扫描逻辑在 bash 里不可测。

## 决定
正文：Markdown。审计脚本：Python 3.11+，只用标准库，纯函数拆到单独模块并配 `unittest`。搭骨架：bash，`set -euo pipefail`。

## 后果
Python < 3.11 的机器跑不了审计脚本（启动即报错，提示版本）。不引入 pytest 等第三方依赖，测试用 `unittest`。
