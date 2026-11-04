# 量化质量门槛

`quality-budget.toml` 是机器读的门槛；本文说明每个值怎么量、怎么配、怎么改。对应标准第 17、18、26 节。

## 默认值

| 键 | 默认 | 含义 |
|---|---|---|
| `project.tier` | 2 | 项目等级 0–3（标准第 0 节）；审计脚本和审查按它缩放要求 |
| `code.warnings` | 0 | 编译 / lint 警告 |
| `code.max_function_lines` | 50 | 函数行数 |
| `code.max_file_lines` | 500 | 文件行数（`audit_project.py` 检查） |
| `code.max_args` | 5 | 函数参数个数 |
| `code.max_cyclomatic_complexity` | 10 | 圈复杂度 |
| `code.max_pr_diff_lines` | 400 | 单次合并 diff 行数（不含锁文件、生成文件） |
| `code.max_duplication_percent` | 3 | 重复代码比例 |
| `tests.pass_rate` | 100 | 测试通过率 |
| `tests.core_line_coverage_min` | 80 | 核心模块行覆盖率 |
| `tests.total_line_coverage_min` | 60 | 总覆盖率 |
| `tests.mutation_kill_rate_min` | 70 | 核心模块变异杀灭率（严格级） |
| `tests.flaky_allowed` | 0 | 允许的不稳定测试数 |
| `deps.high_vulns` | 0 | 高危漏洞数 |
| `deps.license_allow` | MIT, Apache-2.0, BSD-2/3, ISC, MPL-2.0 | 许可证白名单 |
| `todo.overdue_allowed` | 0 | 过期 TODO 数 |
| `resources.*` | 0（未设置） | 设备资源预算，见下 |

## 怎么配

### Rust

`clippy.toml`：
```toml
too-many-lines-threshold = 50
cognitive-complexity-threshold = 10
too-many-arguments-threshold = 5
```
`src/lib.rs` 或 `src/main.rs` 顶部：
```rust
#![warn(clippy::too_many_lines, clippy::cognitive_complexity, clippy::too_many_arguments)]
```
配合 `cargo clippy --all-targets -- -D warnings`，超阈值就是错误。

- 覆盖率：`cargo llvm-cov --fail-under-lines 60`；核心 crate 单独 `cargo llvm-cov -p <core> --fail-under-lines 80`。
- 变异测试：`cargo mutants -p <core>`；杀灭率 = caught / (caught + missed)。
- 依赖：`cargo deny check`（`deny.toml` 写许可证白名单和 advisory 源）、`cargo audit`。
- 属性测试：`proptest`；模糊测试：`cargo fuzz`（需要 nightly）。

### Python

`pyproject.toml`：
```toml
[tool.ruff]
line-length = 120   # 中文字符按宽度 2 计算
[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "C90", "PL", "RUF"]
ignore = ["RUF001", "RUF002", "RUF003"]   # 中文标点会被当成易混淆字符误报
[tool.ruff.lint.mccabe]
max-complexity = 10
[tool.ruff.lint.pylint]
max-args = 5
max-statements = 50
[tool.mypy]
strict = true
```
- 覆盖率：`pytest --cov --cov-fail-under=60`；核心包单独算。
- 变异测试：`mutmut run`。
- 依赖：`pip-audit`；锁文件用 `uv lock` 或 `pip-compile`。
- 属性测试：`hypothesis`。

### 通用

- 骨架、锁文件、CHANGELOG、CLAUDE.md、脚本、文件长度、TODO、密钥痕迹、提交信息：`scripts/audit_project.py`。
- 重复代码：`jscpd --threshold 3 .`（多语言）。
- diff 大小：CI 里 `git diff --stat origin/main...HEAD -- . ':!*.lock' ':!Cargo.lock'`，超 400 行报错。

## 资源预算怎么量（设备、常驻程序）

| 指标 | 测法 |
|---|---|
| 二进制大小 | `ls -l` strip 后的产物 |
| 启动到就绪 | `systemctl start` 到 `--health` 返回 0 的时间差（`date +%s%N`） |
| 空闲 CPU | 启动后稳定 60 s，`pidstat -p <pid> 1 60` 取平均 |
| 空闲 / 峰值 RSS | `ps -o rss= -p <pid>`；峰值看 `/proc/<pid>/status` 的 `VmHWM` |
| 每日写盘 | `/proc/<pid>/io` 的 `write_bytes` 差值换算到 24 h |
| 功耗 | 有功率计时测；没有就不填 |

初始预算 = 实测两次取较差值 × 1.2；之后只许变严。把测法写进 `scripts/smoke.sh`，超预算冒烟失败。

## 改门槛的规矩（Osmani constraint-driven-development 的做法）

- 每个有数字的门槛都对应 ci.sh 里一条会变红的命令。没有命令的数字是愿望。启用前用故意违规的样例确认它真的会红，再用干净样例确认它会绿。
- 棘轮：没有目标值就记录今天的值，规则是"不许变差"。
- 收紧悄悄做（CHANGELOG 一行）；放松必须大声：写 ADR，且不能和导致失败的那个改动同一提交。
- 例外写进 quality-budget.toml 的 `[[exceptions]]`：规则、路径、原因、到期日（≤ 90 天）。审计脚本在到期后报 blocker，缺原因或到期日报 should。
- 至少保留一条外部检查（cargo audit / pip-audit / semgrep 这类不是项目自己写的检查）。
- 审查时盯五种绕过：阈值被移动、测试被弄简单、检查器被静音、工作没做完、凭空出现的例外。审计脚本会列出抑制标记（`#[allow]`、`# noqa`、`eslint-disable` 等）和被跳过的测试，供审查对照。

## 提交门禁

`.githooks/pre-commit` 在每次提交前跑 `scripts/ci.sh`，不绿不提交；克隆后跑一次 `scripts/install-hooks.sh`（设置 `core.hooksPath`）。骨架模板自带，`bootstrap_project.sh` 会自动安装。太慢的步骤挪到 CI，不要关门禁。

## 用 hook 自动执行（可选）

确定性的规则放进 Claude Code 的 hook，比提示词里写"永远记得格式化"可靠。项目的 `.claude/settings.json` 示例：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{"type": "command", "command": "scripts/hook-format.sh"}]
      }
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "echo '收尾前跑 scripts/ci.sh，按第 31 节写变更说明'"}]}
    ]
  }
}
```

`scripts/hook-format.sh` 从标准输入的 JSON 里取 `tool_input.file_path`，按后缀跑 `cargo fmt` / `ruff format` / `shfmt`。hook 只做格式化这类无害、幂等的事；会改语义的操作不放进 hook。

要让"结束前检查必须通过"成为硬规则，`Stop` hook 跑检查脚本并在失败时以退出码 2 结束：Claude Code 会把脚本的 stderr 交回给 Claude 作为"还不能结束"的理由，让它继续修。只有 `command` / `http` 类型的 hook 是确定性的；`prompt` / `agent` 类型是让另一个模型判断，不算强制。强制的 hook 和 deny 规则保持少：每条都会偶尔误触发，都要有人维护；到了几十条，多数该退回成提示。
