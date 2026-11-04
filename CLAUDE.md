@ENGINEERING_STANDARD.md

# engineering-standard（本仓库）

## 这是什么
一个通用的工程标准 skill，给 Claude Code 和读 AGENTS.md 的代理用。本仓库自己是等级 1（工具）项目，按自己的标准来。

## 常用命令
- 全部检查：`scripts/ci.sh`（shell 语法、单元测试、骨架自测、标准自审）
- 单元测试：`python3 -m unittest discover -s scripts -p 'test_*.py'`
- 标准自审：`python3 scripts/audit_project.py .`
- 提交门禁（克隆后跑一次）：`scripts/install-hooks.sh`，之后每次提交自动跑 ci.sh，不绿不提交

## 本仓库特有规则
- 改标准正文（references/ENGINEERING_STANDARD.md）要同时：版本号 +0.1、CHANGELOG 加一条、SKILL.md 文件地图里的行数提示；新增条款要在 sources-review.md 写来源。
- `assets/project-template/` 和 `evals/` 是模板和测试夹具，审计跳过（quality-budget.toml 的 `[audit] skip_paths`）；夹具里的"密码"是故意的测试数据，不是泄露。
- 审计脚本四个文件各 ≤ 500 行：`audit_project.py`（核心与报告）、`audit_structure_checks.py`（骨架与工具链）、`audit_scan_checks.py`（源码扫描）、`audit_source_checks.py`（纯函数、常量，配单元测试）。先 `ruff format` 再数行数。
- 标准里不写任何个人项目的细节；那些放使用者各自项目的 CLAUDE.md。

## 踩过的坑（Gotchas）
- 用 Python 脚本批量改中文文档时，字符串里的 ASCII 双引号会撞上外层引号；一律用三引号。
- 审计脚本手写时压在 500 行内，`ruff format` 一跑变成 766 行；行数要按格式化后的算，拆成了四个模块。

## 汇报
用标准第 31 节的变更说明模板。
