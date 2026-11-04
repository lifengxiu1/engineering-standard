#!/usr/bin/env bash
# 安装提交门禁：让 git 使用仓库里版本化的 .githooks/（core.hooksPath）。每个克隆跑一次。
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
chmod +x .githooks/*
git config core.hooksPath .githooks
echo "已安装提交门禁：提交前自动跑 scripts/ci.sh（core.hooksPath = .githooks）"
