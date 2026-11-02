#!/usr/bin/env bash
# 真机冒烟（标准第 8、18 节）：部署和回滚后必跑。每项一个 check，失败即退出非 0。
# 用法：DEVICE=<ssh 主机> APP=<程序名> [REMOTE_ROOT=/opt/<APP>] scripts/smoke.sh
set -euo pipefail
DEVICE="${DEVICE:?用法: DEVICE=<ssh 主机> APP=<程序名> scripts/smoke.sh}"
APP="${APP:?请设置 APP=<程序名>}"
REMOTE_ROOT="${REMOTE_ROOT:-/opt/$APP}"

check() { # check <名称> <命令...>
  local name="$1"; shift
  printf '%-32s' "$name"
  if "$@" >/dev/null 2>&1; then echo "通过"; else echo "失败"; exit 1; fi
}

check "版本可读"   ssh "$DEVICE" "'$REMOTE_ROOT/current/$APP' --version"
check "健康检查"   ssh "$DEVICE" "'$REMOTE_ROOT/current/$APP' --health"
# TODO(项目): 服务状态、最近 5 分钟无 error 日志、资源预算（空闲 CPU / RSS / 启动时间，见 quality-budget.toml [resources]）
echo "冒烟通过"
