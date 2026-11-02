#!/usr/bin/env python3
"""对照《软件项目工程标准》检查一个仓库，输出按严重度分组的差距清单。

用法:
    python3 audit_project.py [项目目录] [--tier N] [--json] [--today YYYY-MM-DD]

退出码: 0 没有 blocker；1 有 blocker；2 用法或目录错误。需要 Python 3.11+ 和同目录的 audit_source_checks.py。
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    sys.exit("audit_project.py 需要 Python 3.11+（标准库 tomllib）")

from audit_scan_checks import CHECKS as SCAN_CHECKS
from audit_source_checks import HELPER_NAMES, SOURCE_EXT, Finding
from audit_structure_checks import CHECKS as STRUCTURE_CHECKS

SKIP_DIRS = {
    ".git",
    "target",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
}
MAX_TEXT_BYTES = 2 * 1024 * 1024
DEFAULT_TIER = 2
TIER_NAMES = {0: "脚本/实验", 1: "工具/内部", 2: "产品/设备常驻", 3: "安全/运动/金钱"}
ALWAYS_BLOCKER = {"B-SECRET", "B-GIT", "B-BUDGET-PARSE"}
SEVERITY_ORDER = {"blocker": 0, "should": 1, "nit": 2}

# 骨架文件：(相对路径, 从哪个等级起要求, 严重度, 条款, 怎么补)


class Audit:
    def __init__(self, root: Path, today: dt.date, tier_override: int | None = None) -> None:
        self.root = root
        self.today = today
        self.findings: list[Finding] = []
        self.budget = self._load_budget()
        self.files = self._list_files()
        self.tier = self._resolve_tier(tier_override)

    # ---------- 基础 ----------
    def add(self, finding: Finding) -> None:
        self.findings.append(finding)

    def sev(self, severity: str, code: str) -> str:
        """等级 0 的项目把 blocker 降为 should（密钥、git、预算文件解析除外）。"""
        if self.tier == 0 and severity == "blocker" and code not in ALWAYS_BLOCKER:
            return "should"
        return severity

    def _resolve_tier(self, override: int | None) -> int:
        if override is not None:
            return override
        table = self.budget.get("project")
        value = table.get("tier") if isinstance(table, dict) else None
        return value if isinstance(value, int) and value in TIER_NAMES else DEFAULT_TIER

    def _list_files(self) -> list[Path]:
        files: list[Path] = []
        if (self.root / ".git").exists():
            cmd = ["git", "-C", str(self.root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
            try:
                out = subprocess.run(cmd, capture_output=True, check=True).stdout
            except (subprocess.CalledProcessError, FileNotFoundError):
                out = b""
            files = [self.root / p for p in out.decode("utf-8", "replace").split("\0") if p]
        if not files:
            for dirpath, dirnames, filenames in os.walk(self.root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
                files.extend(Path(dirpath) / f for f in filenames)
        skip = tuple(self._skip_paths())
        return [p for p in files if not skip or not self.rel(p).startswith(skip)]

    def _skip_paths(self) -> list[str]:
        """quality-budget.toml 的 [audit] skip_paths：模板、夹具、第三方代码目录，整体跳过审计。"""
        table = self.budget.get("audit")
        value = table.get("skip_paths", []) if isinstance(table, dict) else []
        return [str(v).rstrip("/") + "/" for v in value] if isinstance(value, list) else []

    def _load_budget(self) -> dict[str, Any]:
        text = self.read_text(self.root / "quality-budget.toml")
        if text is None:
            return {}
        try:
            return tomllib.loads(text)
        except ValueError as e:
            self.add(
                Finding(
                    "blocker",
                    "B-BUDGET-PARSE",
                    f"quality-budget.toml 解析失败：{e}",
                    "修成合法 TOML",
                    "§17",
                    "quality-budget.toml",
                )
            )
            return {}

    def exists(self, rel: str) -> bool:
        return (self.root / rel).exists() or (self.root / rel).is_symlink()

    def read_text(self, p: Path) -> str | None:
        try:
            if p.is_symlink() and not p.exists():
                return None
            if not p.is_file() or p.stat().st_size > MAX_TEXT_BYTES:
                return None
            data = p.read_bytes()
        except OSError:
            return None
        if b"\0" in data[:4096]:
            return None
        return data.decode("utf-8", "replace")

    def rel(self, p: Path) -> str:
        return str(p.relative_to(self.root)) if p.is_relative_to(self.root) else str(p)

    def budget_int(self, section: str, key: str, default: int) -> int:
        table = self.budget.get(section)
        value = table.get(key, default) if isinstance(table, dict) else default
        return value if isinstance(value, int) and value > 0 else default

    def _scannable_sources(self) -> list[tuple[Path, str]]:
        out: list[tuple[Path, str]] = []
        for p in self.files:
            if p.suffix not in SOURCE_EXT or p.name in HELPER_NAMES or ".example." in p.name:
                continue
            text = self.read_text(p)
            if text is not None:
                out.append((p, text))
        return out

    # ---------- 骨架与文档 ----------

    # ---------- 源码扫描 ----------

    def run(self) -> list[Finding]:
        for check in (*STRUCTURE_CHECKS, *SCAN_CHECKS):
            check(self)
        self.findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.code, f.where))
        return self.findings


def print_report(root: Path, tier: int, findings: list[Finding]) -> int:
    counts = {s: sum(1 for f in findings if f.severity == s) for s in SEVERITY_ORDER}
    print(f"标准审计  {root}\n项目等级  {tier}（{TIER_NAMES[tier]}）；--tier 或 quality-budget.toml 可改")
    for sev in SEVERITY_ORDER:
        group = [f for f in findings if f.severity == sev]
        print(f"\n{sev} ({len(group)})")
        for f in group:
            where = f"  @ {f.where}" if f.where else ""
            print(f"  [{f.code}] {f.message}{where}")
            print(f"      → {f.fix}  ({f.section})")
    print(f"\n合计：blocker {counts['blocker']}，should {counts['should']}，nit {counts['nit']}")
    print("脚本只查结构性条款；模块边界、错误处理、日志、测试质量仍需对照标准人工审查。")
    return 1 if counts["blocker"] else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="对照工程标准检查一个仓库")
    ap.add_argument("project", nargs="?", default=".", help="项目目录（默认当前目录）")
    ap.add_argument(
        "--tier",
        type=int,
        choices=sorted(TIER_NAMES),
        default=None,
        help="项目等级 0–3；省略时读 quality-budget.toml，再没有按 2",
    )
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--today", default=None, help="判断 TODO 过期用的日期 YYYY-MM-DD（默认今天）")
    args = ap.parse_args(argv)
    root = Path(args.project).resolve()
    if not root.is_dir():
        print(f"不是目录：{root}", file=sys.stderr)
        return 2
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    audit = Audit(root, today, args.tier)
    findings = audit.run()
    if args.json:
        payload = {"project": str(root), "tier": audit.tier, "findings": [asdict(f) for f in findings]}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1 if any(f.severity == "blocker" for f in findings) else 0
    return print_report(root, audit.tier, findings)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
