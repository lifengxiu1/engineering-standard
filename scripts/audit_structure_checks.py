#!/usr/bin/env python3
"""结构性检查：骨架文件、文档、CLAUDE.md、标准副本、脚本、工具链与锁文件、配置、例外。供 audit_project.py 调用。"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from audit_source_checks import (
    CLAUDE_MAX_LINES,
    HELPER_NAMES,
    README_MIN_CHARS,
    SHOW_AT_MOST,
    SKELETON,
    STANDARD_NAME,
    Finding,
    exception_problems,
    python_imports,
    requirement_names,
    standard_version,
    unused_requirements,
)

if TYPE_CHECKING:
    from audit_project import Audit


def check_git(a: Audit) -> None:
    if not (a.root / ".git").exists():
        a.add(Finding("blocker", "B-GIT", "不是 git 仓库", "git init，并把所有东西入库（密钥、产物除外）", "§9"))
    if a.tier >= 1 and not a.exists(".gitignore"):
        a.add(Finding("should", "S-GITIGNORE", "缺少 .gitignore", "至少忽略产物目录、真实配置、密钥、日志", "§9"))


def check_skeleton(a: Audit) -> None:
    for rel, min_tier, sev, section, fix in SKELETON:
        if a.tier < min_tier or a.exists(rel):
            continue
        severity = a.sev(sev, "MISSING")
        a.add(Finding(severity, f"{severity[0].upper()}-MISSING", f"缺少 {rel}", fix, section, rel))
    adr_dir = a.root / "docs" / "adr"
    has_adr1 = adr_dir.is_dir() and any(re.match(r"0*1-.*\.md$", p.name) for p in adr_dir.glob("*.md"))
    if a.tier >= 1 and not has_adr1:
        a.add(
            Finding(
                "should",
                "S-ADR",
                "缺少 docs/adr/0001-language.md（语言选择决策）",
                "按第 2 节写 ADR-0001",
                "§2、§10",
            )
        )


def check_readme(a: Audit) -> None:
    text = a.read_text(a.root / "README.md")
    if text is None:
        return
    if a.tier >= 1 and len(text.strip()) < README_MIN_CHARS:
        a.add(
            Finding(
                "should",
                "S-README-THIN",
                "README.md 太短，说不清四件事",
                "补：是什么、怎么跑、怎么测、怎么部署",
                "§10",
                "README.md",
            )
        )
    if "<一句话" in text:
        a.add(
            Finding("should", "S-README-TEMPLATE", "README.md 还是模板占位内容", "替换尖括号占位符", "§10", "README.md")
        )


def check_changelog(a: Audit) -> None:
    text = a.read_text(a.root / "CHANGELOG.md")
    if text is not None and "## [Unreleased]" not in text:
        a.add(
            Finding(
                "should",
                "S-CHANGELOG-UNRELEASED",
                "CHANGELOG.md 没有 [Unreleased] 段",
                "加 `## [Unreleased]`，每个改动先写进去",
                "§10",
                "CHANGELOG.md",
            )
        )


def check_claude_md(a: Audit) -> None:
    text = a.read_text(a.root / "CLAUDE.md")
    if text is None:
        return
    lines = text.splitlines()
    first = next((ln.strip() for ln in lines if ln.strip()), "")
    if not first.startswith("@" + STANDARD_NAME):
        a.add(
            Finding(
                "should",
                "S-CLAUDE-IMPORT",
                "CLAUDE.md 第一行不是 @ENGINEERING_STANDARD.md",
                "放到第一行，AI 会话才会自动读标准",
                "§0",
                "CLAUDE.md:1",
            )
        )
    if len(lines) > CLAUDE_MAX_LINES:
        a.add(
            Finding(
                "should",
                "S-CLAUDE-LONG",
                f"CLAUDE.md 有 {len(lines)} 行，超过 {CLAUDE_MAX_LINES}",
                "只留每次都需要的规则，其余指向 docs/",
                "§29",
                "CLAUDE.md",
            )
        )


def check_standard_copy(a: Audit) -> None:
    copy = a.root / STANDARD_NAME
    text = a.read_text(copy)
    if text is None:
        return
    default_skill = str(Path.home() / ".claude" / "skills" / "engineering-standard")
    skill_std = Path(os.environ.get("ENGINEERING_STANDARD_SKILL", default_skill)) / "references" / STANDARD_NAME
    if not skill_std.is_file() or skill_std.resolve() == copy.resolve():
        return
    v_copy = standard_version(text)
    v_skill = standard_version(a.read_text(skill_std) or "")
    if v_copy and v_skill and v_copy != v_skill:
        a.add(
            Finding(
                "should",
                "S-STANDARD-OUTDATED",
                f"标准副本版本 {v_copy}，skill 里是 {v_skill}",
                f"cp {skill_std} {STANDARD_NAME}",
                "§0",
                STANDARD_NAME,
            )
        )


def check_scripts(a: Audit) -> None:
    scripts = a.root / "scripts"
    if not scripts.is_dir():
        return
    for p in sorted(scripts.glob("*.sh")):
        rel = a.rel(p)
        if not os.access(p, os.X_OK):
            a.add(Finding("should", "S-SCRIPT-EXEC", f"{rel} 没有可执行位", f"chmod +x {rel}", "§3", rel))
        head = (a.read_text(p) or "").splitlines()[:12]
        if not any("set -euo pipefail" in ln for ln in head):
            a.add(
                Finding(
                    "should",
                    "S-SCRIPT-STRICT",
                    f"{rel} 开头没有 set -euo pipefail",
                    "脚本出错必须立即失败，不能带错继续",
                    "§4",
                    rel,
                )
            )


def check_rust(a: Audit) -> None:
    r = a.root
    if not (r / "Cargo.toml").is_file():
        return
    if not (r / "Cargo.lock").is_file():
        a.add(
            Finding(
                a.sev("blocker", "B-LOCK"),
                "B-LOCK",
                "有 Cargo.toml 但没有 Cargo.lock 入库",
                "cargo generate-lockfile 并提交",
                "§12、§21",
                "Cargo.lock",
            )
        )
    if a.tier < 1:
        return
    if not (r / "rust-toolchain.toml").is_file() and not (r / "rust-toolchain").is_file():
        a.add(
            Finding(
                "should",
                "S-TOOLCHAIN",
                "没有固定 Rust 工具链版本",
                'rust-toolchain.toml 写 channel = "1.xx"',
                "§2、§12",
                "rust-toolchain.toml",
            )
        )
    if not (r / "clippy.toml").is_file():
        a.add(
            Finding(
                "nit",
                "N-CLIPPY-CFG",
                "没有 clippy.toml（函数行数、复杂度、参数阈值）",
                "见 quality-gates.md 的 Rust 段",
                "§4、§17",
                "clippy.toml",
            )
        )
    if not (r / "deny.toml").is_file():
        a.add(
            Finding(
                "nit", "N-DENY-CFG", "没有 deny.toml（许可证白名单、漏洞源）", "cargo deny init", "§21", "deny.toml"
            )
        )


def check_python(a: Audit) -> None:
    r = a.root
    has_pyproject = (r / "pyproject.toml").is_file()
    py_files = [p for p in a.files if p.suffix == ".py" and p.name not in HELPER_NAMES]
    if not has_pyproject and not py_files:
        return
    locks = ["uv.lock", "poetry.lock", "pdm.lock", "requirements.txt", "requirements.lock"]
    if has_pyproject and not any((r / name).is_file() for name in locks):
        a.add(Finding("should", "S-PYLOCK", "Python 依赖没有锁文件", "uv lock / pip-compile，并提交", "§12、§21"))
    if a.tier >= 1 and has_pyproject and not (r / ".python-version").is_file():
        a.add(
            Finding(
                "should",
                "S-PYVERSION",
                "没有 .python-version 固定解释器版本",
                "echo 3.12 > .python-version",
                "§2、§12",
                ".python-version",
            )
        )
    req = a.read_text(r / "requirements.txt")
    if req is None:
        return
    unpinned = [
        ln.strip() for ln in req.splitlines() if ln.strip() and not ln.startswith(("#", "-")) and "==" not in ln
    ]
    if unpinned:
        shown = ", ".join(unpinned[:SHOW_AT_MOST])
        message = f"requirements.txt 有 {len(unpinned)} 个未固定版本的依赖：{shown}"
        a.add(
            Finding(
                "should",
                "S-PY-UNPINNED",
                message,
                "固定到 == 版本，或改用 uv/pip-compile 生成锁文件",
                "§21",
                "requirements.txt",
            )
        )


def check_other_locks(a: Audit) -> None:
    r = a.root
    js_locks = ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"]
    if (r / "package.json").is_file() and not any((r / name).is_file() for name in js_locks):
        a.add(
            Finding(
                a.sev("blocker", "B-LOCK"),
                "B-LOCK",
                "有 package.json 但没有锁文件入库",
                "npm install 生成 package-lock.json 并提交",
                "§12、§21",
                "package.json",
            )
        )
    if (r / "go.mod").is_file() and not (r / "go.sum").is_file():
        a.add(
            Finding(
                a.sev("blocker", "B-LOCK"),
                "B-LOCK",
                "有 go.mod 但没有 go.sum",
                "go mod tidy 并提交",
                "§12、§21",
                "go.sum",
            )
        )


def check_config(a: Audit) -> None:
    cfg = a.root / "config"
    if not cfg.is_dir():
        return
    files = [p for p in cfg.iterdir() if p.is_file()]
    if files and all(".example." not in p.name for p in files):
        a.add(
            Finding(
                "should",
                "S-CONFIG-EXAMPLE",
                "config/ 里没有 *.example.* 示例配置",
                "入库示例配置，真实配置加入 .gitignore",
                "§11",
                "config/",
            )
        )


def check_exceptions(a: Audit) -> None:
    """quality-budget.toml 的 [[exceptions]]：必须有原因和到期日，到期即 blocker（第 17 节）。"""
    kinds = {
        "no_reason": ("should", "S-EXCEPTION-NO-REASON", "补 reason"),
        "no_expiry": ("should", "S-EXCEPTION-NO-EXPIRY", "补 expires（≤ 90 天）"),
        "expired": ("blocker", "B-EXCEPTION-EXPIRED", "修掉问题并删除例外，或写 ADR 续期"),
    }
    for kind, message in exception_problems(a.budget.get("exceptions"), a.today):
        severity, code, fix = kinds[kind]
        a.add(Finding(severity, code, message, fix, "§17", "quality-budget.toml"))


def check_python_unused_deps(a: Audit) -> None:
    """requirements.txt 里声明了、源码里却没 import 的包（第 21 节：不为用不到的东西加依赖）。"""
    req = a.read_text(a.root / "requirements.txt")
    if req is None:
        return
    imports: set[str] = set()
    for p, text in a._scannable_sources():
        if p.suffix == ".py":
            imports |= python_imports(text)
    unused = unused_requirements(requirement_names(req), imports)
    if unused:
        shown = ", ".join(unused[:SHOW_AT_MOST])
        a.add(
            Finding(
                "nit",
                "N-PY-UNUSED-DEP",
                f"requirements.txt 里 {len(unused)} 个包没被 import：{shown}",
                "删掉没用的依赖；包名和模块名不一致的属误报，可忽略",
                "§21",
                "requirements.txt",
            )
        )


def check_commit_gate(a: Audit) -> None:
    """有 .githooks/pre-commit 却没装（core.hooksPath 未指向它）：门禁等于没有（第 9 节）。"""
    if a.tier < 1 or not (a.root / ".githooks" / "pre-commit").is_file() or not (a.root / ".git").exists():
        return
    cmd = ["git", "-C", str(a.root), "config", "--get", "core.hooksPath"]
    try:
        hooks_path = subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.strip()
    except FileNotFoundError:
        return
    if hooks_path != ".githooks":
        a.add(
            Finding(
                "should",
                "S-HOOKS-NOT-INSTALLED",
                "有 .githooks/pre-commit 但没安装，提交不会跑检查",
                "scripts/install-hooks.sh（每个克隆一次）",
                "§9",
                ".githooks/pre-commit",
            )
        )


CHECKS = (
    check_git,
    check_skeleton,
    check_readme,
    check_changelog,
    check_claude_md,
    check_standard_copy,
    check_scripts,
    check_rust,
    check_python,
    check_other_locks,
    check_config,
    check_exceptions,
    check_python_unused_deps,
    check_commit_gate,
)
