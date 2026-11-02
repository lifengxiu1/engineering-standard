#!/usr/bin/env bash
# 一条命令回滚到上一个版本（标准第 12 节）：current ← previous，重启，冒烟。
# 用法：DEVICE=<ssh 主机> APP=<程序名> [REMOTE_ROOT=/opt/<APP>] scripts/rollback.sh
# shellcheck disable=SC2029  # 远程命令里的变量在本机展开是有意的：路径和版本由本机决定
set -euo pipefail
cd "$(dirname "$0")/.."
DEVICE="${DEVICE:?用法: DEVICE=<ssh 主机> APP=<程序名> scripts/rollback.sh}"
APP="${APP:?请设置 APP=<程序名>}"
REMOTE_ROOT="${REMOTE_ROOT:-/opt/$APP}"

ssh "$DEVICE" "cd '$REMOTE_ROOT' && [ -L previous ]" || { echo "设备上没有 previous，无法回滚" >&2; exit 1; }
ssh "$DEVICE" "cd '$REMOTE_ROOT' && target=\$(readlink previous) && ln -sfn \"\$target\" current && echo \"current -> \$target\""

restart_service() {
  # TODO(项目): 重启服务，和 deploy.sh 里一致
  echo "TODO: 填写 scripts/rollback.sh 的 restart_service()" >&2
  return 2
}
restart_service

scripts/smoke.sh
echo "回滚完成"
