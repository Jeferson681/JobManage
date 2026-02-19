#!/usr/bin/env python3
"""Check Python files for usage of `sqlite3.connect` outside allowlisted paths.

Usage: pre-commit will pass filenames as args.
"""
import os
import re
import sys
from pathlib import Path

# Allowlist prefixes for `sqlite3.connect` checks. To avoid committing local
# private directory names to the repository, allow overriding with
# `SQLITE_ALLOWLIST` (comma-separated prefixes). Defaults keep tools/scripts
# and the storage layer allowed.
env_sql_allow = os.environ.get("SQLITE_ALLOWLIST", "")
if env_sql_allow:
    ALLOWLIST = tuple(x.strip() for x in env_sql_allow.split(",") if x.strip())
else:
    ALLOWLIST = (
        "tests/",
        "src/jobmanager/storage/",
        # intentionally open DB connections from these helpers
        "src/jobmanager/api/app.py",
        "src/jobmanager/worker/runner.py",
        "tools/",
        "scripts/",
    )

PAT = re.compile(r"\bsqlite3\.connect\b")


def is_allowed(path: str) -> bool:
    """Return True when `path` is in the allowlist paths."""
    p = path.replace("\\", "/")
    for a in ALLOWLIST:
        if p.startswith(a) or f"/{a}" in p:
            return True
    return False


def main(argv: list[str]) -> int:
    """Run check over provided filenames and return exit code suitable for pre-commit."""
    bad = []
    for fn in argv:
        if not fn.endswith(".py"):
            continue
        if is_allowed(fn):
            continue
        try:
            txt = Path(fn).read_text(encoding="utf-8")
        except Exception:
            continue
        if PAT.search(txt):
            bad.append(fn)

    if bad:
        print("Detected `sqlite3.connect` in files outside allowlist:")
        for b in bad:
            print(" -", b)
        print("\nIf this usage is intentional, add an allowlist exception in scripts/check_sqlite_connect.py")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
