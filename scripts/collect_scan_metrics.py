#!/usr/bin/env python3
"""Collect scan metrics from trufflehog JSON and sqlite check report.

Usage:
  python scripts/collect_scan_metrics.py <trufflehog_json> <sqlite_report_txt> <out_json>

Produces a JSON object with counts: {"sqlite_findings": N, "trufflehog_findings": M}
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def count_sqlite_findings(path: Path) -> int:
    """Return number of sqlite findings recorded in the checker output file.

    The checker writes one line per finding starting with '- '.
    """
    if not path.exists():
        return 0
    try:
        txt = path.read_text(encoding="utf-8")
    except Exception:
        return 0
    # The sqlite checker prints lines starting with ' - <file>' for each finding
    return sum(1 for line in txt.splitlines() if line.strip().startswith("- "))


def count_truffle_findings(path: Path) -> int:
    """Return the number of trufflehog findings in the JSON report.

    Handles list-form or object-with-"findings" formats.
    """
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    # trufflehog may emit a list or an object with 'findings'
    if isinstance(data, dict) and "findings" in data and isinstance(data["findings"], list):
        return len(data["findings"])
    if isinstance(data, list):
        return len(data)
    # single object
    return 1


def main(argv: list[str]) -> int:
    """CLI entrypoint: <trufflehog_json> <sqlite_report_txt> <out_json>.

    Returns exit code 0 on success.
    """
    if len(argv) != 3:
        print("Usage: collect_scan_metrics.py <trufflehog_json> <sqlite_report_txt> <out_json>")
        return 2
    truffle, sqlite, out = map(Path, argv)
    metrics = {
        "sqlite_findings": count_sqlite_findings(sqlite),
        "trufflehog_findings": count_truffle_findings(truffle),
    }
    try:
        out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    except Exception as exc:  # pragma: no cover - IO
        print("Failed to write metrics:", exc)
        return 3
    print(f"Wrote metrics to {out}: {metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
