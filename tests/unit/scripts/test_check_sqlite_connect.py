import os
import sys
from pathlib import Path

# Ensure repo root is first on sys.path so `import scripts.*` resolves here
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import scripts.check_sqlite_connect as checker


def test_check_detects_outside_allowlist(tmp_path):
    bad_file = tmp_path / "bad_usage.py"
    bad_file.write_text('import sqlite3\nsqlite3.connect("db.sqlite3")\n')

    rc = checker.main([str(bad_file)])
    assert rc == 1


def test_check_ignores_allowlisted_file(tmp_path):
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    allowed = scripts_dir / "allowed_usage_tmp.py"
    allowed.write_text('import sqlite3\nsqlite3.connect("db.sqlite3")\n')

    try:
        rc = checker.main([str(allowed)])
        assert rc == 0
    finally:
        try:
            allowed.unlink()
        except OSError:
            pass
