#!/usr/bin/env bash
# 把 dist/ 的产物部署到设备（标准第 12、24 节）：
# 校验 → 装到 releases/<版本> → 记住 previous → 切换 current → 重启 → 冒烟；冒烟失败自动回滚。幂等。
# 用法：DEVICE=<ssh 主机> APP=<程序名> [REMOTE_ROOT=/opt/<APP>] scripts/deploy.sh
# shellcheck disable=SC2029  # 远程命令里的变量在本机展开是有意的：路径和版本由本机决定
set -euo pipefail
cd "$(dirname "$0")/.."
DEVICE="${DEVICE:?用法: DEVICE=<ssh 主机> APP=<程序名> scripts/deploy.sh}"
APP="${APP:?请设置 APP=<程序名>}"
REMOTE_ROOT="${REMOTE_ROOT:-/opt/$APP}"
VERSION=$(cat dist/VERSION)

echo "部署 $APP $VERSION → $DEVICE:$REMOTE_ROOT"
ssh "$DEVICE" "mkdir -p '$REMOTE_ROOT/releases/$VERSION'"
scp -rq dist/. "$DEVICE:$REMOTE_ROOT/releases/$VERSION/"
ssh "$DEVICE" "cd '$REMOTE_ROOT/releases/$VERSION' && sha256sum -c --quiet SHA256SUMS"
ssh "$DEVICE" "cd '$REMOTE_ROOT' && { [ -L current ] && cp -P current previous || true; } && ln -sfn 'releases/$VERSION' current"

restart_service() {
  # TODO(项目): 重启服务，例如：ssh "$DEVICE" "systemctl --user restart $APP.service"
  echo "TODO: 填写 scripts/deploy.sh 的 restart_service()" >&2
  return 2
}
restart_service

if ! scripts/smoke.sh; then
  echo "冒烟失败，自动回滚" >&2
  scripts/rollback.sh
  exit 1
fi
echo "部署完成：$APP $VERSION"
