#!/usr/bin/env python3
"""纯函数检查，不做 IO，供 audit_project.py 调用，可单独测试（test_audit_source_checks.py）。

覆盖：密钥痕迹、TODO 日期、shortcut 债务标记、检查器抑制标记与被跳过的测试、测试里的固定 sleep、
标准副本版本、quality-budget.toml 的例外条目；另放各检查模块共用的常量、骨架清单和 Finding 类型。
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

SOURCE_EXT = {".rs", ".py", ".go", ".ts", ".tsx", ".js", ".c", ".cc", ".cpp", ".h", ".hpp", ".sh", ".kt", ".java"}
UPGRADE_WORDS = ("升级", "upgrade", "触发")

TODO_RE = re.compile(r"\b(TODO|FIXME|XXX)\b(?:\((\d{4}-\d{2}-\d{2})[^)]*\))?")
SHORTCUT_RE = re.compile(r"\bshortcut:\s*(.+)$")
STANDARD_VERSION_RE = re.compile(r"^版本\s+(\d+\.\d+)")
SECRET_PATTERNS = [
    ("私钥", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("API key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("硬编码密码/令牌", re.compile(r"(?i)\b(?:password|passwd|secret|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]")),
]
# (标签, 模式, 是否为"跳过测试")。被跳过的测试按标准第 8 节必须带原因和到期日，所以单独报。
SUPPRESSION_PATTERNS = [
    ("#[allow]", re.compile(r"#!?\[allow\("), False),
    ("#[ignore]", re.compile(r"#\[ignore\b"), True),
    ("noqa", re.compile(r"#\s*noqa\b"), False),
    ("type: ignore", re.compile(r"#\s*type:\s*ignore\b"), False),
    ("pytest skip/xfail", re.compile(r"@pytest\.mark\.(?:skip|skipif|xfail)\b"), True),
    ("unittest skip", re.compile(r"@unittest\.skip\w*\("), True),
    ("eslint-disable", re.compile(r"eslint-disable"), False),
    ("ts-ignore", re.compile(r"@ts-(?:ignore|expect-error)\b"), False),
    ("js test skip", re.compile(r"\b(?:it|test|describe)\.skip\(|\bx(?:it|test|describe)\("), True),
    ("nolint", re.compile(r"//\s*nolint\b"), False),
    ("nosemgrep", re.compile(r"\bnosemgrep\b"), False),
    ("gitleaks:allow", re.compile(r"gitleaks:allow"), False),
]
SLEEP_RE = re.compile(r"\b(?:time\.sleep|thread::sleep|tokio::time::sleep|asyncio\.sleep|time\.Sleep)\(\s*([^)]*)\)")
ZERO_ARG_RE = re.compile(r"^(?:0|0\.0+|0_f64|Duration::ZERO)?$")
IMPORT_RE = re.compile(r"^\s*(?:import\s+([\w.]+)|from\s+([\w.]+)\s+import\b)", re.M)
REQ_NAME_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")
NONATOMIC_WRITE_RE = re.compile(r"\b(?:std::)?fs::write\(|\bFile::create\(")
# 包名与 import 名不一致的常见情况（都已标准化为小写、下划线）
IMPORT_ALIASES = {
    "pyyaml": "yaml",
    "scikit_learn": "sklearn",
    "pillow": "pil",
    "beautifulsoup4": "bs4",
    "python_dateutil": "dateutil",
    "opencv_python": "cv2",
    "psycopg2_binary": "psycopg2",
    "attrs": "attr",
}
TEST_NAME_RE = re.compile(r"^(?:test_.*\.py|.*_test\.(?:py|go)|.*\.(?:test|spec)\.[jt]sx?)$")

STANDARD_NAME = "ENGINEERING_STANDARD.md"
HELPER_NAMES = {
    "audit_project.py",
    "audit_source_checks.py",
    "audit_structure_checks.py",
    "audit_scan_checks.py",
    "test_audit_source_checks.py",
}
LARGE_FILE_BYTES = 1024 * 1024
README_MIN_CHARS = 200
CLAUDE_MAX_LINES = 100
DEFAULT_MAX_FILE_LINES = 500
RECENT_COMMITS = 20
SHOW_AT_MOST = 5
COMMIT_RE = re.compile(r"^(feat|fix|docs|refactor|test|perf|chore|build|ci|style|revert)(\([^)]+\))?!?: ")
SKELETON = [
    ("README.md", 0, "blocker", "§3、§10", "写清：是什么、怎么跑、怎么测、怎么部署"),
    ("CHANGELOG.md", 1, "blocker", "§10", "Keep a Changelog 格式，含 [Unreleased] 段"),
    ("CLAUDE.md", 1, "blocker", "§3、§29", "第一行 @ENGINEERING_STANDARD.md，≤ 100 行"),
    (STANDARD_NAME, 1, "blocker", "§0", "从 skill 复制标准副本"),
    ("scripts/ci.sh", 1, "blocker", "§12、§17", "一条命令跑完格式、lint、测试、审计"),
    ("LICENSE", 1, "should", "§3", "开源选 MIT/Apache-2.0；不开源写 All rights reserved"),
    ("AGENTS.md", 1, "should", "§0", "ln -s CLAUDE.md AGENTS.md"),
    ("quality-budget.toml", 1, "should", "§17", "从 skill 模板复制并按项目填写"),
    ("docs/pitfalls.md", 1, "should", "§10、§27", "失误登记表"),
    ("docs/architecture.md", 2, "should", "§3、§28", "模块图、状态机、安全状态、单点故障清单"),
    ("docs/runbook.md", 2, "should", "§10", "部署、回滚、看日志、error 对照表"),
    ("docs/release-checklist.md", 2, "should", "§24", "发布清单"),
    ("scripts/build.sh", 2, "should", "§12", "一条命令出带版本和校验和的产物"),
    ("scripts/deploy.sh", 2, "should", "§12", "幂等部署，保留上一版本，部署后冒烟"),
    ("scripts/rollback.sh", 2, "should", "§12", "一条命令回滚"),
    ("scripts/smoke.sh", 2, "should", "§8、§18", "真机冒烟，含资源预算检查"),
    ("scripts/audit_project.py", 1, "nit", "§3", "从 skill 复制全部四个 audit_*.py，让 ci.sh 能跑标准审计"),
]


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    fix: str
    section: str
    where: str = ""


def standard_version(text: str) -> str | None:
    """标准文件前 10 行里的"版本 X.Y"。"""
    for ln in text.splitlines()[:10]:
        m = STANDARD_VERSION_RE.match(ln.strip())
        if m:
            return str(m.group(1))
    return None


def secret_hits(text: str) -> list[tuple[str, int]]:
    """每行最多报一个命中：(类别, 行号)。"""
    hits: list[tuple[str, int]] = []
    for i, ln in enumerate(text.splitlines(), 1):
        for label, pat in SECRET_PATTERNS:
            if pat.search(ln):
                hits.append((label, i))
                break
    return hits


def todo_states(text: str, today: dt.date) -> dict[str, list[int]]:
    """TODO/FIXME/XXX 按状态分组的行号：overdue（带日期且已过）、undated（无日期或日期非法）、ok。"""
    found: dict[str, list[int]] = {"overdue": [], "undated": [], "ok": []}
    for i, ln in enumerate(text.splitlines(), 1):
        for m in TODO_RE.finditer(ln):
            found[_todo_state(m.group(2), today)].append(i)
    return found


def _todo_state(date: str | None, today: dt.date) -> str:
    if not date:
        return "undated"
    try:
        return "overdue" if dt.date.fromisoformat(date) < today else "ok"
    except ValueError:
        return "undated"


def shortcut_hits(text: str) -> tuple[list[int], list[int]]:
    """shortcut: 标记的行号：(写了升级条件的, 没写的)。"""
    with_trigger: list[int] = []
    without: list[int] = []
    for i, ln in enumerate(text.splitlines(), 1):
        m = SHORTCUT_RE.search(ln)
        if m is None:
            continue
        (with_trigger if any(w in m.group(1) for w in UPGRADE_WORDS) else without).append(i)
    return with_trigger, without


def suppression_hits(text: str) -> list[tuple[str, int, bool]]:
    """检查器抑制标记：(标签, 行号, 是否跳过测试)。每行最多一个。"""
    hits: list[tuple[str, int, bool]] = []
    for i, ln in enumerate(text.splitlines(), 1):
        for label, pat, is_skip in SUPPRESSION_PATTERNS:
            if pat.search(ln):
                hits.append((label, i, is_skip))
                break
    return hits


def sleep_hits(text: str) -> list[int]:
    """固定等待的行号。sleep(0) 这类让出调度的写法不算。"""
    hits: list[int] = []
    for i, ln in enumerate(text.splitlines(), 1):
        for m in SLEEP_RE.finditer(ln):
            if not ZERO_ARG_RE.match(m.group(1).strip()):
                hits.append(i)
                break
    return hits


def exception_problems(entries: object, today: dt.date) -> list[tuple[str, str]]:
    """[[exceptions]] 条目的问题：(类型, 描述)。类型：no_reason / no_expiry / expired（标准第 17 节）。"""
    problems: list[tuple[str, str]] = []
    if not isinstance(entries, list):
        return problems
    for i, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            continue
        label = f"exceptions[{i}] {entry.get('rule', '?')} @ {entry.get('path', '?')}"
        if not entry.get("reason"):
            problems.append(("no_reason", f"{label} 没写原因"))
        expires = entry.get("expires")
        if expires is None:
            problems.append(("no_expiry", f"{label} 没写到期日"))
            continue
        expiry = expires if isinstance(expires, dt.date) else _parse_date(str(expires))
        if expiry is not None and expiry < today:
            problems.append(("expired", f"{label} 已于 {expiry} 到期"))
    return problems


def _parse_date(value: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None


def python_imports(text: str) -> set[str]:
    """源码里 import 的顶层模块名（小写）：import a.b → a；from a.b import c → a。"""
    return {(m.group(1) or m.group(2)).split(".")[0].lower() for m in IMPORT_RE.finditer(text)}


def requirement_names(text: str) -> list[str]:
    """requirements.txt 里的包名，去掉版本、注释、选项行，标准化为小写下划线。"""
    out: list[str] = []
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln or ln.startswith(("#", "-")):
            continue
        m = REQ_NAME_RE.match(ln)
        if m:
            out.append(m.group(1).lower().replace("-", "_").replace(".", "_"))
    return out


def unused_requirements(names: list[str], imports: set[str]) -> list[str]:
    """声明了但没被 import 的包；考虑常见的包名 / 模块名不一致。"""
    lowered = {i.lower() for i in imports}
    return [n for n in names if n not in lowered and IMPORT_ALIASES.get(n, n) not in lowered]


def nonatomic_write_hits(text: str) -> list[int]:
    """直接覆盖写文件的行号（Rust 的 fs::write / File::create）。状态文件该用 临时文件 → fsync → rename。"""
    return [i for i, ln in enumerate(text.splitlines(), 1) if NONATOMIC_WRITE_RE.search(ln)]


def is_test_file(path: Path, text: str) -> bool:
    """按路径和内容判断是不是测试文件：tests/ 目录、test_*.py、*_test.go、*.test.ts、含 #[test] 的 .rs。"""
    if "tests" in path.parts or TEST_NAME_RE.match(path.name):
        return True
    return path.suffix == ".rs" and "#[test]" in text
