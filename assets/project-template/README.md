# <项目名>

<一句话：这是什么，运行在哪。>

## 怎么跑
<安装依赖、配置文件（复制 config/config.example.toml）、启动命令。>

## 怎么测
```bash
scripts/ci.sh
```

## 怎么部署
```bash
scripts/build.sh                      # 构建机上
DEVICE=<主机> APP=<程序名> scripts/deploy.sh
DEVICE=<主机> APP=<程序名> scripts/rollback.sh   # 回滚
```
详细步骤和故障处理见 docs/runbook.md。

## 文档
- 架构、状态机、安全状态：docs/architecture.md
- 决策记录：docs/adr/
- 更新日志：CHANGELOG.md
- 工程标准：ENGINEERING_STANDARD.md
