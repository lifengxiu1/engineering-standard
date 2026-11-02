#!/usr/bin/env bash
# 本仓库的全部检查：shell 语法、单元测试、骨架自测、标准自审。本地和 CI 都用它。
# 用法：scripts/ci.sh            缺少可选工具只警告
#       STRICT=1 scripts/ci.sh   CI：缺少工具也算失败
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
missing=()
step() { printf '\n== %s\n' "$*"; }
run() { if "$@"; then :; else echo "!! 失败: $*"; fail=1; fi; }
need() { if command -v "$1" >/dev/null 2>&1; then return 0; fi; echo "-- 缺少 $1（安装：$2）"; missing+=("$1"); return 1; }

step "Shell 语法"
for f in scripts/*.sh assets/project-template/scripts/*.sh; do run bash -n "$f"; done
if need shellcheck "apt install shellcheck"; then step "shellcheck"; run shellcheck scripts/*.sh assets/project-template/scripts/*.sh; fi

step "Python 编译"
run python3 -m py_compile scripts/audit_project.py scripts/audit_source_checks.py scripts/test_audit_source_checks.py
if need ruff "pip install ruff"; then step "ruff"; run ruff check scripts; run ruff format --check scripts; fi

step "单元测试"
run python3 -m unittest discover -s scripts -p 'test_*.py'

step "骨架自测（空目录 bootstrap 后审计应无 blocker）"
tmp=$(mktemp -d)
if bash scripts/bootstrap_project.sh "$tmp/demo" >/dev/null && python3 scripts/audit_project.py "$tmp/demo" >/dev/null; then
  echo "通过"
else
  echo "!! 骨架自测失败"; fail=1
fi
rm -rf "$tmp"

step "标准自审（本仓库，等级 1）"
run python3 scripts/audit_project.py .

rm -rf scripts/__pycache__
echo
if [ "${#missing[@]}" -gt 0 ]; then
  echo "缺少的工具: ${missing[*]}"
  if [ "${STRICT:-0}" = "1" ]; then echo "STRICT=1：缺少工具按失败处理"; fail=1; fi
fi
if [ "$fail" -ne 0 ]; then echo "结果：失败"; exit 1; fi
echo "结果：全部通过"
