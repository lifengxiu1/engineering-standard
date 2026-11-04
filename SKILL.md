---
name: engineering-standard
description: 使用者所有软件项目的强制工程标准与工作流（高标准：按硬件选语言、模块化、结构化日志、测试与 CI、变更文档、量化质量门槛、断电安全、AI 作者与 AI 审查规则、完成的定义）。凡是为使用者做软件工程工作——新建项目、搭仓库骨架、写或改代码、修 bug、代码审查 / review、修 bug / 排错 / debug / 测试挂了、发布 / 部署 / 回滚、补文档或 CHANGELOG、评估一个项目的质量、"按标准来"、"高标准"——都要先用本 skill，即使用户没有提到"标准"二字。Mandatory engineering standard for all of this user's software; use it for project bootstrap, repo audits, code changes, code review, release and definition-of-done checks, even when the user does not say "standard".
---

# engineering-standard

这是一套对使用者所有软件项目生效的工程标准。它存在的原因：代码主要由 AI 写，不同会话、不同模型如果各凭感觉，质量就不稳定；有了一份写清楚为什么、能逐条打勾、按项目等级缩放的默认标准，每次会话和每个审查者对照的就是同一个东西。

它是默认值，不是法典：偏向谨慎而不是速度，小任务用判断力，但把判断说出来（变更说明里一句"跳过了什么"）。它借鉴了 Karpathy 的 LLM 编码四原则和 ponytail 的"最少代码"阶梯，见文末。

## 文件地图

| 文件 | 什么时候读 |
|---|---|
| `references/ENGINEERING_STANDARD.md` | 完整标准 v1.4（约 550 行，顶部有目录）。按需读相关章节，不必每次通读：`grep -n '^## ' references/ENGINEERING_STANDARD.md` 找行号，`sed -n 'A,Bp'` 读某一节 |
| `references/review-protocol.md` | 做审查或请求审查时 |
| `references/quality-gates.md` | 填 `quality-budget.toml`、配 lint 阈值、覆盖率、变异测试、资源预算测量、例外与 hook 时 |
| `references/sources-review.md` | 想知道某条规则从哪来、为什么取或弃了某个外部 skill 时 |
| `assets/project-template/` | 新项目骨架；`bootstrap_project.sh` 复制它 |
| `scripts/bootstrap_project.sh <目录>` | 新项目，或给老项目补骨架。已有文件一律不覆盖 |
| `scripts/audit_project.py <目录> [--tier N]` | 对照标准检查仓库：骨架、锁文件、CHANGELOG、CLAUDE.md、脚本、TODO、shortcut 债务台账、抑制标记、跳过的测试、测试 sleep、例外到期、文件长度、密钥痕迹、提交信息。按项目等级缩放，按严重度分组输出；有 blocker 退出码 1。同目录另外三个 `audit_*.py` 是它的模块 |

## 先判断是哪种工作

- 新项目、空目录、"搭骨架" → 工作流 A
- 已有项目第一次按标准看、"评估一下"、"哪里不达标" → 工作流 B
- 写功能、修 bug、重构（日常开发） → 工作流 C
- "审查 / review 这个改动" → 工作流 D
- 发布、部署、"能不能发" → 工作流 E
- 修 bug、测试挂了、"为什么不对"、性能退化 → 工作流 F

每种工作流都只读标准里相关的章节。标准第 1 节的九条原则和第 29 节的 AI 作者规则在任何工作流里都适用。

动手前先定**项目等级**（标准第 0 节的表）：0 脚本 / 实验，1 工具 / 内部，2 产品 / 设备常驻，3 安全 / 运动 / 金钱。等级写在 `quality-budget.toml` 的 `[project] tier`，没有的话按上下文判断并在汇报里说明。等级 0 的一次性脚本不需要骨架、CHANGELOG、审查；例如智能台灯固件是 2，导航机器人是 3。不确定选高一级。

## 工作流 A：新项目

1. 从上下文确定运行环境（MCU / Linux 单板 / 服务器 / 脚本）、硬件约束、已有语言。按标准第 2 节的表选语言，理由写进 ADR-0001。信息不够就问；用户不在线就按表选并在汇报里写明假设。
2. 跑 `bash ~/.claude/skills/engineering-standard/scripts/bootstrap_project.sh <目录>`。它复制骨架、放入标准副本和 `audit_project.py`、建 `AGENTS.md -> CLAUDE.md`、需要时 `git init`，并安装提交门禁（提交前自动跑 `scripts/ci.sh`）。
3. 填 `docs/adr/0001-language.md`、`quality-budget.toml`（含 `[project] tier`，其余见 quality-gates.md）、`CLAUDE.md` 的项目段、`README.md` 四件事。
4. 让 `scripts/ci.sh` 在空项目上跑绿；让空程序能启动、打日志、`--version`、`--health`、优雅退出。**这一步和第 5 步需要工具链**（cargo、ruff 之类）。本机没有的话，止步于第 3 步，写明"第 4、5 步等有工具链的机器做"，不要在编译不了的机器上写几百行没验证过的代码（第 29 节：验证后再说完成；评测里有 skill 的运行曾这样花了 35 分钟）。
5. 填 build / deploy / rollback / smoke 四个脚本，在目标设备上部署一次 Hello 版本并实际回滚一次。
6. 跑 `python3 scripts/audit_project.py .`，blocker 清零。
7. 以上全部完成后才写第一个功能。顺序就是标准附录 B；跳步会在后面加倍还债。

## 工作流 B：审计现有项目

1. 先跑 `python3 ~/.claude/skills/engineering-standard/scripts/audit_project.py <目录> --tier N` 拿结构性差距（N 按项目等级；省略时读 quality-budget.toml，再没有就按 2）。
2. 再对照标准第 4–13 节和第 15–28 节看脚本查不到的：模块边界、错误处理、日志、测试层次、断电安全、并发、资源预算。每条给 文件:行号。
3. 输出差距清单：严重度（blocker / should / nit）、条款号、位置、建议。这一步不动代码。清单最多 20 条：blocker 全列，should / nit 合并同类项；每条一两句，不展开成段落。
4. 和用户确认优先级后，每个差距一个独立提交修复，按工作流 C 走。
5. 审计结果存 `docs/metrics/YYYY-MM-DD-audit.md`，作为以后对比的基线。

## 工作流 C：做改动（日常开发）

1. **开工条件（第 15 节）**：写出目标、验收标准、非目标、影响范围、测试计划、回滚方案。用户不在线就按最保守解释执行并记下假设。
2. **定级（第 16 节）**：S / M / L。M 以上先写设计便签到 `docs/design/`，第一个提交是设计不是代码。
3. 开工前读项目 `CLAUDE.md`、`docs/pitfalls.md`、`docs/runbook.md`。
4. 写代码前先走第 4 节的阶梯：真的需要吗 → 仓库里有吗 → 标准库有吗 → 平台原生有吗 → 已装依赖有吗 → 能一行吗 → 才写最少能用的。先读改动触及的代码，列出所有要改到的地方。
5. 实现，遵守第 4–8 节。外科手术式改动：每一行都能追溯到任务要求，不顺便改旁边的东西，看到无关问题提一句不动手。修 bug 先写复现测试。刻意的捷径用 `shortcut:` 标记并写明升级条件。等级 2 起默认测试先行：先写会失败的测试、亲眼看它失败、再写最少的代码让它通过，一次一个切片。
6. 自检：`scripts/ci.sh` 全绿；对照第 13 节清单逐条自查；CHANGELOG 的 `[Unreleased]` 加一行；文档同提交改。
7. 验证后再说完成：声称测试通过、构建成功、bug 修好之前，必须在本条消息里新跑对应命令并读完输出；"应该、大概、似乎"是停下来跑命令的信号。然后用第 31 节模板写变更说明，附真实命令和输出。没跑的写"未验证"，跳过的流程写"跳过了什么"。
8. 请求独立审查（工作流 D）。每条发现逐条回应。等级 0 自审即可。
9. 对照第 14 节完成的定义（按等级缩放），全部打勾才说"完成"。

## 工作流 D：审查改动

读 `references/review-protocol.md`，按它的提示词和输出格式做。要点：
- 先要齐四样输入：标准、diff、变更说明、测试输出。缺就要，不猜。
- 机器已查的（格式、lint、测试）不讨论；先确认它们是绿的。
- 每条发现：严重度、文件:行号、问题、违反条款、建议。问题一句、失败场景一句、建议一句，不展开成段落；超过 20 条合并同类项。不复述，不表扬，没有 blocker 就明说。
- 在 Claude Code 里，作者会话之外用 `/code-review`（L 级改动用 `/code-review ultra`）作为独立审查者；或把 review-protocol.md 的提示词交给另一个模型。

## 工作流 E：发布

1. 对照 `docs/release-checklist.md`（第 24 节）逐项打勾；任何一项没过不发。
2. 在构建机上构建，产物带版本、git 哈希、SHA256；设备只安装产物。
3. 先 1 台设备，跑 `scripts/smoke.sh`，观察一个完整使用周期；发布前写明回滚判据。
4. 记录发布（CHANGELOG 版本段或 `docs/releases/`），存健康度快照到 `docs/metrics/`。

## 工作流 F：修 bug / 排错

按标准第 8 节的排错六步，顺序不能跳：
1. 建反馈回路：一条命令能在这个 bug 上稳定变红。建不出来就说明试了什么，要环境、要日志或要加探针的许可，不先猜。
2. 复现并最小化，确认红的是用户报的那个症状，不是旁边的。
3. 读完整报错和栈；查最近改动（回归用 `git bisect`）；对比仓库里能工作的相似代码，列出所有差异。
4. 写 3–5 个可证伪的假设并排序，一次只改一个变量验证。
5. 根因找到后：先写回归测试看它红 → 只修根因 → 测试绿 → 全量测试 → 回路再跑一次。3 次修不好停下来和用户谈架构，不试第 4 次。
6. 清理调试日志（带唯一前缀的）和临时脚本，提交信息写根因，变更说明按第 31 节。

## 汇报规则

- 汇报永远用第 31 节的变更说明模板。
- 验证了什么、怎么验证的、没验证什么，三项必写。模拟 / 本地 / dry-run 通过不等于真机通过。
- 密钥不出现在回复里。需要用户输密码时给一条可直接运行的命令，结果自己读。

## 什么时候可以不遵守

规则是默认值。三种合法的"不遵守"：
- 项目等级低（0 或 1），对应条款本来就不生效，不用解释。
- 单次判断跳过某一步（比如 20 行改动不写设计便签），在变更说明的"跳过了什么"里写一句理由。
- 长期对某个项目关闭某条，写一条 ADR 说明为什么、影响什么、什么时候回头；必要时改标准本身。
悄悄违反是唯一不合法的方式。

## 借鉴来源

- Andrej Karpathy 对 LLM 编码失误的观察，经 forrestchang/andrej-karpathy-skills 整理成四条：想清楚再动手、最少的代码、外科手术式改动、目标驱动执行。进入了标准第 1、4、15、29 节。
- Dietrich Gebert 的 ponytail："最好的代码是没写的代码"、写代码前的阶梯、懒而不是省、shortcut 标记与债务台账、每次回复末尾披露跳过了什么、审查优先级"正确 > 安全 > 负载 > 测试 > 快 > 精简"。进入了标准第 4、13 节和审计脚本。
- Jesse Vincent 的 superpowers：红-绿-重构的铁律（没看着测试失败就不知道它测的对不对）、排错四阶段、"没有本条消息里新跑的证据不得声称完成"、收审查意见先核实再改。进入了标准第 8、13、15、16、29 节。
- Matt Pocock 的 skills：审问式澄清（决策树、只问当前能答的、每问附推荐答案）、曳光弹式 TDD、六阶段排错（先建反馈回路）、双轴审查、PR 的证据与可逆性。进入了第 8、13、15、31 节。
- Addy Osmani 的 agent-skills：约束驱动开发（没有命令的数字是愿望、棘轮、例外到期、五种绕过）、五轴审查、完成的定义里"代码实际运行过"。进入了第 13、14、17、21 节和审计脚本。
- Trail of Bits 的 skills：静态分析进 CI、安全改动用第二模型再审、依赖供应链审计。进入了第 12 节（等级 3）。
- Claude Code 官方最佳实践与 shanraisshan 的实战汇总：给 AI 一条能跑的检查、早纠偏、确定性规则进 hook 和 settings 而不是提示词、CLAUDE.md 保持短。进入了第 29 节和 quality-gates.md。
- 取舍理由逐条见 `references/sources-review.md`。想直接装原版：`/plugin marketplace add forrestchang/andrej-karpathy-skills`、`DietrichGebert/ponytail`、`obra/superpowers-marketplace`、`mattpocock/skills`，都和本 skill 不冲突。

## 维护本 skill

- 标准升级：改 `references/ENGINEERING_STANDARD.md`，版本号 +0.1，顶部注明日期；然后到每个项目重新复制副本（`bootstrap_project.sh` 不覆盖已有文件，副本要手动 `cp`），并更新项目里的 `scripts/audit_project.py` 副本。
- 新项目类型（网页、手机端等）出现时，在第 2 节加行、在第三部分加专项，而不是另写一份标准。
- 测试用例在 `evals/`，可用 `claude plugin eval` 跑。
