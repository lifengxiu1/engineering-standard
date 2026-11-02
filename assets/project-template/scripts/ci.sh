#!/usr/bin/env bash
# 一条命令跑完：格式、lint、测试、审计、标准审计。本地和 CI 都用它。
# 用法：scripts/ci.sh            本地：缺少可选工具只警告
#       STRICT=1 scripts/ci.sh   CI：缺少工具也算失败
set -euo pipefail
cd "$(dirname "$0")/.."

fail=0
missing=()
step() { printf '\n== %s\n' "$*"; }
run() { if "$@"; then :; else echo "!! 失败: $*"; fail=1; fi; }
need() { # need <命令> <安装提示>
  if command -v "$1" >/dev/null 2>&1; then return 0; fi
  echo "-- 缺少 $1（安装：$2）"; missing+=("$1"); return 1
}

# ---------- Rust ----------
if [ -f Cargo.toml ]; then
  step "Rust: 格式";   run cargo fmt --all -- --check
  step "Rust: clippy"; run cargo clippy --all-targets --locked -- -D warnings
  step "Rust: 测试";   run cargo test --locked
  if need cargo-deny "cargo install cargo-deny --locked"; then step "Rust: 依赖许可与漏洞"; run cargo deny check; fi
  if need cargo-audit "cargo install cargo-audit --locked"; then step "Rust: 漏洞审计"; run cargo audit; fi
fi

# ---------- Python ----------
if [ -f pyproject.toml ] || [ -n "$(find . -name '*.py' -not -path './.venv/*' -not -path './.git/*' -not -path './scripts/*' -print -quit)" ]; then
  if need ruff "pip install ruff"; then
    step "Python: 格式"; run ruff format --check .
    step "Python: lint"; run ruff check .
  fi
  if need mypy "pip install mypy"; then step "Python: 类型"; run mypy .; fi
  if need pytest "pip install pytest"; then step "Python: 测试"; run pytest -q; fi
  if need pip-audit "pip install pip-audit"; then step "Python: 漏洞审计"; run pip-audit; fi
fi

# ---------- Go ----------
if [ -f go.mod ]; then
  step "Go: 格式"; unformatted=$(gofmt -l .); if [ -n "$unformatted" ]; then echo "$unformatted"; fail=1; fi
  step "Go: vet";  run go vet ./...
  step "Go: 测试"; run go test ./...
fi

# ---------- Shell ----------
if need shellcheck "apt install shellcheck"; then
  step "Shell: shellcheck"
  find . -name '*.sh' -not -path './.git/*' -not -path './target/*' -not -path './.venv/*' -print0 | xargs -0 -r shellcheck || fail=1
fi

# ---------- 密钥扫描 ----------
if need gitleaks "https://github.com/gitleaks/gitleaks/releases"; then
  step "密钥扫描"; run gitleaks detect --source . --no-banner
fi

# ---------- 标准审计（骨架、锁文件、CHANGELOG、TODO、文件长度、密钥痕迹）----------
step "标准审计"
run python3 scripts/audit_project.py .

# ---------- 结果 ----------
echo
if [ "${#missing[@]}" -gt 0 ]; then
  echo "缺少的工具: ${missing[*]}"
  if [ "${STRICT:-0}" = "1" ]; then echo "STRICT=1：缺少工具按失败处理"; fail=1; fi
fi
if [ "$fail" -ne 0 ]; then echo "结果：失败"; exit 1; fi
echo "结果：全部通过"
