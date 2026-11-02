#!/usr/bin/env bash
# 在构建机上一条命令出产物（标准第 12 节）。设备上禁止运行本脚本。
# 产物放 dist/：程序、VERSION、SHA256SUMS。
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "0.0.0-dev")
GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "nogit")
BUILD_TIME=$(date -u +%FT%TZ)
OUT=dist
export APP_VERSION="$VERSION" APP_GIT_HASH="$GIT_HASH" APP_BUILD_TIME="$BUILD_TIME"
echo "版本 $VERSION  提交 $GIT_HASH  时间 $BUILD_TIME"
rm -rf "$OUT" && mkdir -p "$OUT"

build() {
  # TODO(项目): 按主语言填写，并把三个 APP_* 变量编进 --version 输出。例如 Rust：
  #   cargo build --release --locked
  #   cp target/release/<程序名> "$OUT/"
  echo "TODO: 填写 scripts/build.sh 的 build() 函数" >&2
  return 2
}
build

echo "$VERSION" > "$OUT/VERSION"
( cd "$OUT" && sha256sum -- * > SHA256SUMS )
echo "产物在 $OUT/，校验和见 $OUT/SHA256SUMS"
