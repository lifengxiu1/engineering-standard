#!/usr/bin/env python3
"""源码扫描类检查：测试、文件长度、TODO、shortcut、抑制标记、测试 sleep、密钥、大文件、提交信息。"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from audit_source_checks import (
    COMMIT_RE,
    DEFAULT_MAX_FILE_LINES,
    HELPER_NAMES,
    LARGE_FILE_BYTES,
    RECENT_COMMITS,
    SHOW_AT_MOST,
    STANDARD_NAME,
    Finding,
    is_test_file,
    nonatomic_write_hits,
    secret_hits,
    shortcut_hits,
    sleep_hits,
    suppression_hits,
    todo_states,
)

if TYPE_CHECKING:
    from audit_project import Audit


def check_tests(a: Audit) -> None:
    has_tests = any(is_test_file(p, text) for p, text in a._scannable_sources()) or any(
        p.is_file() and p.name != ".gitkeep" for p in (a.root / "tests").rglob("*")
    )
    has_source = any(p.suffix != ".sh" for p, _ in a._scannable_sources())
    if not has_source or has_tests:
        return
    if a.tier == 0:
        a.add(
            Finding(
                "nit",
                "N-NO-TESTS",
                "没有测试（等级 0 不强制）",
                "有分支、循环、解析、钱或安全的逻辑写一个小测试",
                "§8",
            )
        )
    else:
        a.add(
            Finding(
                "blocker",
                "B-NO-TESTS",
                "有源码但找不到任何测试",
                "至少为核心逻辑写单元测试；修 bug 先写复现测试",
                "§8",
            )
        )


def check_file_length(a: Audit) -> None:
    max_lines = a.budget_int("code", "max_file_lines", DEFAULT_MAX_FILE_LINES)
    long_files = [(len(text.splitlines()), a.rel(p)) for p, text in a._scannable_sources()]
    for n, rel in sorted((f for f in long_files if f[0] > max_lines), reverse=True)[:10]:
        a.add(
            Finding("should", "S-FILE-LONG", f"{rel} 有 {n} 行，超过 {max_lines}", "按职责拆成多个模块", "§4、§17", rel)
        )


def check_todos(a: Audit) -> None:
    overdue: list[str] = []
    undated: list[str] = []
    for p, text in a._scannable_sources():
        states = todo_states(text, a.today)
        overdue += [f"{a.rel(p)}:{n}" for n in states["overdue"]]
        undated += [f"{a.rel(p)}:{n}" for n in states["undated"]]
    if overdue:
        shown = ", ".join(overdue[:SHOW_AT_MOST])
        a.add(
            Finding(
                a.sev("blocker", "B-TODO-OVERDUE"),
                "B-TODO-OVERDUE",
                f"{len(overdue)} 个过期 TODO：{shown}",
                "做掉，或改日期并说明原因",
                "§4、§17",
                overdue[0],
            )
        )
    if undated:
        shown = ", ".join(undated[:SHOW_AT_MOST])
        a.add(
            Finding(
                "should",
                "S-TODO-UNDATED",
                f"{len(undated)} 个没有日期的 TODO/FIXME：{shown}",
                "写成 TODO(YYYY-MM-DD 主题): ...，或做掉",
                "§4",
                undated[0],
            )
        )


def check_shortcuts(a: Audit) -> None:
    """shortcut: 标记 = 刻意的捷径（ponytail）。汇总成债务台账；没写升级条件的单独标出。"""
    ledger: list[str] = []
    no_trigger: list[str] = []
    for p, text in a._scannable_sources():
        with_trigger, without = shortcut_hits(text)
        ledger += [f"{a.rel(p)}:{n}" for n in with_trigger]
        no_trigger += [f"{a.rel(p)}:{n}" for n in without]
    if no_trigger:
        shown = ", ".join(no_trigger[:SHOW_AT_MOST])
        a.add(
            Finding(
                "should",
                "S-SHORTCUT-NO-TRIGGER",
                f"{len(no_trigger)} 个 shortcut 没写升级条件：{shown}",
                "补上 `升级: <什么情况下怎么改>`，否则它会烂在代码里",
                "§4",
                no_trigger[0],
            )
        )
    if ledger:
        shown = ", ".join(ledger[:SHOW_AT_MOST])
        a.add(
            Finding(
                "nit",
                "N-SHORTCUT-LEDGER",
                f"债务台账：{len(ledger)} 个刻意捷径：{shown}",
                "每次发布前过一遍，到了触发条件的做掉",
                "§4、§26",
                ledger[0],
            )
        )


def check_suppressions(a: Audit) -> None:
    """检查器抑制标记台账（第 17 节的"检查器被静音"）；被跳过的测试按第 8 节要有原因和到期日。"""
    skips: list[str] = []
    others: list[str] = []
    for p, text in a._scannable_sources():
        for label, n, is_skip in suppression_hits(text):
            (skips if is_skip else others).append(f"{a.rel(p)}:{n} ({label})")
    if skips:
        shown = ", ".join(skips[:SHOW_AT_MOST])
        a.add(
            Finding(
                "should",
                "S-TEST-SKIPPED",
                f"{len(skips)} 处跳过的测试：{shown}",
                "修好或删掉；必须跳过的写明原因和到期日",
                "§8、§17",
                skips[0].split(" ")[0],
            )
        )
    if others:
        shown = ", ".join(others[:SHOW_AT_MOST])
        a.add(
            Finding(
                "nit",
                "N-SUPPRESSION-LEDGER",
                f"抑制标记台账：{len(others)} 处：{shown}",
                "审查时逐个核对有没有理由注释；没有的就是绕过检查",
                "§4、§17",
                others[0].split(" ")[0],
            )
        )


def check_test_sleeps(a: Audit) -> None:
    hits: list[str] = []
    for p, text in a._scannable_sources():
        if is_test_file(p, text):
            hits += [f"{a.rel(p)}:{n}" for n in sleep_hits(text)]
    if hits:
        shown = ", ".join(hits[:SHOW_AT_MOST])
        a.add(
            Finding(
                "should",
                "S-TEST-SLEEP",
                f"{len(hits)} 处测试里用固定 sleep 等待：{shown}",
                "改成条件轮询（等到状态满足或超时），固定等待既慢又不稳",
                "§8",
                hits[0],
            )
        )


def check_secrets(a: Audit) -> None:
    hits: list[tuple[str, str]] = []
    for p in a.files:
        if p.name in HELPER_NAMES or p.name == STANDARD_NAME or ".example." in p.name:
            continue
        text = a.read_text(p)
        if text is not None:
            hits.extend((label, f"{a.rel(p)}:{i}") for label, i in secret_hits(text))
    for label, where in hits[:RECENT_COMMITS]:
        a.add(
            Finding(
                "blocker",
                "B-SECRET",
                f"疑似{label}写在仓库里",
                "移到环境变量或权限 600 的文件；已泄露的立即轮换",
                "§11",
                where,
            )
        )


def check_large_files(a: Audit) -> None:
    for p in a.files:
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > LARGE_FILE_BYTES and p.is_file() and not p.is_symlink():
            a.add(
                Finding(
                    "should",
                    "S-LARGE-FILE",
                    f"{a.rel(p)} 有 {size // LARGE_FILE_BYTES} MB",
                    "大二进制用 LFS 或放仓库外",
                    "§9",
                    a.rel(p),
                )
            )


def check_commits(a: Audit) -> None:
    if a.tier < 1 or not (a.root / ".git").exists():
        return
    cmd = ["git", "-C", str(a.root), "log", "-n", str(RECENT_COMMITS), "--format=%s"]
    try:
        out = subprocess.run(cmd, capture_output=True, check=True, text=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return
    subjects = [s for s in out.splitlines() if s.strip()]
    bad = [s for s in subjects if not COMMIT_RE.match(s)]
    if bad:
        a.add(
            Finding(
                "nit",
                "N-COMMIT-MSG",
                f"最近 {len(subjects)} 条提交中 {len(bad)} 条不符合 Conventional Commits，例如 {bad[0][:60]!r}",
                "feat(scope): ... / fix: ... / docs: ...",
                "§9",
            )
        )


def check_nonatomic_writes(a: Audit) -> None:
    """Rust 里直接覆盖写文件的调用台账（第 19 节：状态文件要 临时文件 → fsync → rename）。"""
    hits: list[str] = []
    for p, text in a._scannable_sources():
        if p.suffix == ".rs" and not is_test_file(p, text):
            hits += [f"{a.rel(p)}:{n}" for n in nonatomic_write_hits(text)]
    if hits:
        shown = ", ".join(hits[:SHOW_AT_MOST])
        a.add(
            Finding(
                "nit",
                "N-NONATOMIC-WRITE",
                f"{len(hits)} 处直接覆盖写文件（fs::write / File::create）：{shown}",
                "写的是状态或配置文件就改成 临时文件 → fsync → rename；日志、产物可忽略",
                "§19",
                hits[0],
            )
        )


CHECKS = (
    check_tests,
    check_file_length,
    check_todos,
    check_shortcuts,
    check_suppressions,
    check_test_sleeps,
    check_secrets,
    check_large_files,
    check_commits,
    check_nonatomic_writes,
)
