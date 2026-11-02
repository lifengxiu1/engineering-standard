#!/usr/bin/env python3
"""audit_source_checks 的单元测试。运行：python3 -m unittest discover -s scripts -p 'test_*.py'"""

from __future__ import annotations

import datetime as dt
import unittest
from pathlib import Path

from audit_source_checks import (
    exception_problems,
    is_test_file,
    secret_hits,
    shortcut_hits,
    sleep_hits,
    standard_version,
    suppression_hits,
    todo_states,
)

TODAY = dt.date(2026, 11, 2)


class SecretHitsTest(unittest.TestCase):
    def test_reports_password_and_private_key_once_per_line(self) -> None:
        text = 'password = "hunter2hunter2"\nok = 1\n-----BEGIN RSA PRIVATE KEY-----\n'
        self.assertEqual([("硬编码密码/令牌", 1), ("私钥", 3)], secret_hits(text))

    def test_ignores_short_values_and_env_lookups(self) -> None:
        self.assertEqual([], secret_hits('password = "abc"\ntoken = os.environ["TOKEN"]\n'))


class TodoStatesTest(unittest.TestCase):
    def test_classifies_overdue_undated_and_ok(self) -> None:
        text = "// TODO(2026-01-01 x): old\n// TODO: none\n// FIXME(2027-01-01): later\n// TODO(bad-date): x\n"
        states = todo_states(text, TODAY)
        self.assertEqual({"overdue": [1], "undated": [2, 4], "ok": [3]}, states)


class ShortcutHitsTest(unittest.TestCase):
    def test_splits_by_upgrade_trigger(self) -> None:
        text = "// shortcut: 线性查找; 上限: 1000; 升级: 改哈希表\n// shortcut: 先写死 5 秒\nx = 1\n"
        self.assertEqual(([1], [2]), shortcut_hits(text))


class SuppressionHitsTest(unittest.TestCase):
    def test_marks_test_skips_separately(self) -> None:
        text = "#[allow(dead_code)]\n#[ignore]\nx = 1  # noqa: E501\n@pytest.mark.skip(reason='x')\nit.skip('a')\n"
        hits = suppression_hits(text)
        self.assertEqual(
            [
                ("#[allow]", 1, False),
                ("#[ignore]", 2, True),
                ("noqa", 3, False),
                ("pytest skip/xfail", 4, True),
                ("js test skip", 5, True),
            ],
            hits,
        )


class SleepHitsTest(unittest.TestCase):
    def test_reports_fixed_waits_but_not_yield_sleeps(self) -> None:
        text = "time.sleep(2)\nawait asyncio.sleep(0)\nthread::sleep(Duration::from_millis(50));\ntime.sleep(0.0)\n"
        self.assertEqual([1, 3], sleep_hits(text))


class ExceptionProblemsTest(unittest.TestCase):
    def test_flags_missing_fields_and_expiry(self) -> None:
        entries = [
            {"rule": "a", "path": "x", "reason": "r", "expires": dt.date(2026, 1, 1)},
            {"rule": "b", "path": "y", "expires": "2027-01-01"},
            {"rule": "c", "path": "z", "reason": "r"},
            "not a table",
        ]
        kinds = [k for k, _ in exception_problems(entries, TODAY)]
        self.assertEqual(["expired", "no_reason", "no_expiry"], kinds)
        self.assertEqual([], exception_problems(None, TODAY))


class IsTestFileTest(unittest.TestCase):
    def test_detects_by_path_name_and_rust_attribute(self) -> None:
        self.assertTrue(is_test_file(Path("tests/integration.py"), ""))
        self.assertTrue(is_test_file(Path("pkg/test_x.py"), ""))
        self.assertTrue(is_test_file(Path("pkg/x_test.go"), ""))
        self.assertTrue(is_test_file(Path("src/lib.rs"), "fn a() {}\n#[test]\nfn t() {}"))
        self.assertFalse(is_test_file(Path("src/lib.rs"), "fn a() {}"))
        self.assertFalse(is_test_file(Path("src/main.py"), ""))


class StandardVersionTest(unittest.TestCase):
    def test_reads_version_from_header(self) -> None:
        self.assertEqual("1.2", standard_version("# 标题\n\n版本 1.2 · 2026-11-02 · x\n"))
        self.assertIsNone(standard_version("no version here\n"))


if __name__ == "__main__":
    unittest.main()
