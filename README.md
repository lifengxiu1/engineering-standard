# engineering-standard

一套给 AI 写代码用的工程标准，做成了 Claude Code skill，也能被任何读 `AGENTS.md` 的代码代理使用。

**它解决的问题**：代码越来越多由 AI 写。不同会话、不同模型各凭感觉，质量就不稳定。这里有一份写清楚为什么、能逐条打勾、按项目等级缩放的默认标准，再配两个脚本把能机器检查的部分自动化。

**它不是什么**：不是法典。规则偏向谨慎而不是速度，小任务用判断力，但跳过了什么要说出来；每条规则都能用一条决策记录对某个项目关闭。

## 主要内容

- **项目等级 0–3**：一次性脚本只要几条规矩，长期运行的设备服务用全套，会动会伤人的最严。
- **写代码前的阶梯**：真的需要吗 → 仓库里有吗 → 标准库有吗 → 平台原生有吗 → 已装依赖有吗 → 能一行吗 → 才写最少能用的。
- **外科手术式改动**：每一行改动都能追溯到任务要求。
- **测试先行**（等级 2 起）：先写会失败的测试，亲眼看它失败，再写最少的代码让它通过。
- **排错六步**：先建一条能变红的反馈回路，再假设；根因找到才修；三次修不好停下来谈架构。
- **验证后再说完成**：声称通过之前必须在同一条消息里新跑检查并读完输出。
- **独立审查**：换模型或换会话审，发现带文件和行号，作者逐条回应。
- **约束驱动的质量门槛**：没有检查命令的数字是愿望；棘轮；例外必须带到期日。
- **设备专项**：断电安全、看门狗、安全状态、无网无时钟、升级回滚、故障注入清单。
- **完成的定义**和固定格式的**变更说明**（验证了什么、没验证什么、跳过了什么、可逆性）。

## 安装

Claude Code（个人级，所有项目可用）：

```bash
git clone https://github.com/lifengxiu1/engineering-standard.git ~/.claude/skills/engineering-standard
```

其他代理（Codex、Cursor、Copilot 等）：把 `references/ENGINEERING_STANDARD.md` 复制到项目根目录，在项目的 `AGENTS.md` 或 `CLAUDE.md` 第一行写 `@ENGINEERING_STANDARD.md`。`scripts/bootstrap_project.sh <目录>` 会把这些和整套骨架一起放好。

需要 Python 3.11+（审计脚本用标准库 `tomllib`）和 bash。

## 用法

skill 会在做软件工程工作时自动加载；也可以直接说：

| 你说 | 它走 |
|---|---|
| "新建一个项目 X" | 工作流 A：选语言、搭骨架、填质量预算、让空程序先能跑能回滚 |
| "评估一下这个项目" | 工作流 B：跑审计脚本 + 对照标准人工看，输出差距清单，不动代码 |
| "加个功能 / 重构" | 工作流 C：开工条件 → 定级 → 阶梯 → 实现 → 变更说明 → 审查 |
| "审查这个改动" | 工作流 D：按审查协议，表格输出，作者逐条回应 |
| "能不能发布" | 工作流 E：发布清单，先一台设备观察一个周期 |
| "修这个 bug" | 工作流 F：排错六步 |

手动用脚本：

```bash
# 在空目录或老项目里搭骨架（不覆盖已有文件）
bash ~/.claude/skills/engineering-standard/scripts/bootstrap_project.sh ./my-project

# 对照标准审计一个仓库；--tier 0..3，省略时读 quality-budget.toml
python3 ~/.claude/skills/engineering-standard/scripts/audit_project.py ./my-project --tier 2
```

## 仓库结构

```
SKILL.md                         入口：六个工作流、读哪个文件
references/ENGINEERING_STANDARD.md   标准正文（核心 15 节 + 严格级 13 节 + 设备专项 + AI 规则）
references/review-protocol.md    审查协议与可粘贴的审查者提示词
references/quality-gates.md      量化门槛怎么配、怎么量、例外与 hook
references/sources-review.md     借鉴了哪些外部 skills，取了什么、弃了什么、为什么
assets/project-template/         新项目骨架（28 个文件）
scripts/bootstrap_project.sh     搭骨架
scripts/audit_*.py               审计脚本：核心、结构检查、源码扫描、纯函数（配单元测试）
evals/                           三个测试用例（claude plugin eval 可跑）
```

本仓库自己按自己的标准来：等级 1，`scripts/ci.sh` 跑单元测试和标准自审。

## 借鉴来源

Andrej Karpathy 的 LLM 编码四原则（forrestchang/andrej-karpathy-skills）、Dietrich Gebert 的 ponytail、Jesse Vincent 的 superpowers、Matt Pocock 和 Addy Osmani 的 skills、Trail of Bits 的安全 skills、Claude Code 官方最佳实践。每一家取了什么、弃了什么，见 `references/sources-review.md`；出处见标准附录 A。

## English

An engineering standard for AI-written software, packaged as a Claude Code skill and usable by any agent that reads `AGENTS.md`. It scales by project tier (0 script → 3 safety/motion/money), favors the smallest change that works, requires tests first from tier 2, a six-step root-cause debugging loop, fresh verification evidence before any "done" claim, independent review with file:line findings, constraint-driven quality gates (a number without a command is a wish), and device rules (power loss, watchdog, safe state, rollback). Two scripts: `bootstrap_project.sh` scaffolds a project without overwriting; `audit_project.py` checks a repo against the standard and fails CI on blockers. Content is in Chinese.

## License

MIT.
