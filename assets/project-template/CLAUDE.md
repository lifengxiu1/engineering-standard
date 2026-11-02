@ENGINEERING_STANDARD.md

# 项目说明（保持 ≤ 100 行；只放每次会话都需要的内容，其余指向 docs/）

## 这是什么
<一句话。运行在什么硬件 / 环境。主语言及理由见 docs/adr/0001-language.md。>
项目等级：<0–3，见 ENGINEERING_STANDARD.md 第 0 节；与 quality-budget.toml 的 [project] tier 一致>

## 常用命令
- 全部检查（格式、lint、测试、审计）：`scripts/ci.sh`
- 构建产物（只在构建机上）：`scripts/build.sh`
- 部署 / 回滚：`DEVICE=<主机> APP=<程序名> scripts/deploy.sh` / `scripts/rollback.sh`
- 真机冒烟：`scripts/smoke.sh`
- 标准审计：`python3 scripts/audit_project.py .`

## 本项目特有规则
<例如：设备上禁止编译；日志不写扩展卡；某个总线只有一个写者；安全状态是什么。>

## 踩过的坑（Gotchas）
<AI 自己读代码发现不了的事：集成测试需要哪个环境变量、哪个目录不能碰、哪个工具版本有问题。纠正过两次的事一定写进来。>

## 开工前读
- docs/pitfalls.md（失误登记）
- docs/runbook.md（运维）
- docs/architecture.md（模块、状态机、安全状态）

## 汇报
用 ENGINEERING_STANDARD.md 第 31 节的变更说明模板；写明验证了什么、怎么验证的、没验证什么。
