#!/usr/bin/env bash
# 用 engineering-standard skill 的骨架初始化（或补全）一个项目。已有文件一律不覆盖。
# 用法：bootstrap_project.sh <项目目录>
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$SKILL_DIR/assets/project-template"
TARGET_ARG="${1:?用法: bootstrap_project.sh <项目目录>}"
mkdir -p "$TARGET_ARG"
TARGET="$(cd "$TARGET_ARG" && pwd)"

copied=()
skipped=()
copy_one() { # copy_one <源文件> <目标相对路径>
  local src="$1" rel="$2" dst="$TARGET/$2"
  if [ -e "$dst" ] || [ -L "$dst" ]; then skipped+=("$rel"); return 0; fi
  mkdir -p "$(dirname "$dst")"
  cp -p "$src" "$dst"
  copied+=("$rel")
}

# 1. 骨架
while IFS= read -r -d '' f; do
  copy_one "$f" "${f#"$TEMPLATE"/}"
done < <(find "$TEMPLATE" -type f -print0 | sort -z)

# 2. 标准副本 + 审计脚本副本（让项目的 ci.sh 不依赖 skill 路径）
copy_one "$SKILL_DIR/references/ENGINEERING_STANDARD.md" "ENGINEERING_STANDARD.md"
for f in audit_project.py audit_source_checks.py audit_structure_checks.py audit_scan_checks.py; do
  copy_one "$SKILL_DIR/scripts/$f" "scripts/$f"
done

# 3. AGENTS.md -> CLAUDE.md，给其他 AI 工具
if [ -e "$TARGET/AGENTS.md" ] || [ -L "$TARGET/AGENTS.md" ]; then
  skipped+=("AGENTS.md")
else
  ln -s CLAUDE.md "$TARGET/AGENTS.md"
  copied+=("AGENTS.md -> CLAUDE.md")
fi

# 4. 可执行位
chmod +x "$TARGET"/scripts/*.sh "$TARGET"/scripts/audit_*.py 2>/dev/null || true

# 5. git
if [ ! -d "$TARGET/.git" ]; then
  git -C "$TARGET" init -q -b main 2>/dev/null || git -C "$TARGET" init -q
  echo "已 git init（$TARGET）"
fi
# 6. 提交门禁：提交前自动跑 scripts/ci.sh
if [ -x "$TARGET/scripts/install-hooks.sh" ]; then
  (cd "$TARGET" && bash scripts/install-hooks.sh)
fi

# 报告
echo "新建 ${#copied[@]} 个文件："
for f in "${copied[@]}"; do echo "  $f"; done
if [ "${#skipped[@]}" -gt 0 ]; then
  echo "已存在、未覆盖 ${#skipped[@]} 个："
  for f in "${skipped[@]}"; do echo "  $f"; done
fi
cat <<'NEXT'

下一步（标准附录 B，按顺序）：
  1. 填 docs/adr/0001-language.md、quality-budget.toml、CLAUDE.md 项目段、README.md
  2. 固定工具链（rust-toolchain.toml / .python-version），生成锁文件
  3. scripts/ci.sh 跑绿；python3 scripts/audit_project.py . 清零 blocker
  4. 空程序能启动、打日志、--version、--health、优雅退出
  5. build / deploy / rollback / smoke 四个脚本填好，在设备上部署一次并实际回滚一次
  6. 以上全部通过后，才写第一个功能
NEXT
