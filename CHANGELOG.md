# 更新日志

格式遵循 Keep a Changelog，版本号遵循语义化版本。标准正文的"版本 X.Y"与这里的 X.Y.0 对应。

## [Unreleased]

## [1.4.0] - 2026-11-03

### Added
- 提交门禁：`.githooks/pre-commit` 提交前跑 `scripts/ci.sh`，`scripts/install-hooks.sh` 安装；骨架模板自带，bootstrap 自动安装；审计报“有钩子没安装”；标准第 9 节写入条款（版本 1.4）
- 审计新增两项 nit：requirements.txt 里声明了却没 import 的包（§21）、Rust 里直接覆盖写文件的调用台账（§19）

### Changed
- 审计清单和审查发现设上限：最多 20 条，blocker 全列，should / nit 合并同类项，每条一两句（评测显示有 skill 的运行比基线慢 3–9 倍，产出过长是原因之一）
- 评测断言：搭骨架用例在无 cargo 的机器上允许只剩 B-LOCK
- 工作流 A：本机没有工具链时止步于骨架 + ADR + 预算 + README，空程序四件事留到有工具链的机器（评测发现有 skill 的运行在无 cargo 的机器上写了 566 行未编译代码）

### Fixed
- 审计的 TODO 正则只认 `TODO:` / `TODO(...):` 写法，注释里提到这个词不再误报（模板 ci.sh 的注释曾让每个新项目自带一条 should）
- 评测夹具 change.diff 的 hunk 头行数（+25 → +24），现在能被 git apply 直接应用

## [1.3.0] - 2026-11-02

### Changed
- 标准里的个人项目细节改为通用说法（设备示例、不可信介质、构建机），项目特有的事实移到各项目的 CLAUDE.md
- 开源：补齐 README、LICENSE（MIT）、CHANGELOG、CI、仓库自身的审计配置（等级 1）

### Added
- 审计脚本支持 `quality-budget.toml` 的 `[audit] skip_paths`，跳过模板、夹具、第三方代码目录

## [1.2.0] - 2026-11-02

### Added
- 融合 superpowers、mattpocock/skills、addyosmani/agent-skills、trailofbits/skills、Claude Code 官方实践：测试先行、排错六步、验证后再说完成、约束驱动门槛、双轴审查、可逆性、hook 强制
- 审计脚本拆成 `audit_project.py` + `audit_source_checks.py`，新增例外到期、跳过的测试、测试里的固定 sleep、抑制标记台账四项检查，附单元测试
- 工作流 F：修 bug / 排错；`references/sources-review.md` 评估记录

## [1.1.0] - 2026-11-01

### Added
- 项目等级 0–3，规则按等级缩放；"小事用判断力，但要说出来"
- 融合 Karpathy 四原则与 ponytail 的阶梯、shortcut 债务台账、披露习惯

## [1.0.0] - 2026-11-01

### Added
- 标准 v1.0：核心 15 节、严格级 13 节、设备专项、AI 作者与审查规则、完成的定义
- SKILL.md 五个工作流、项目骨架模板、bootstrap 与审计脚本、三个评测用例
