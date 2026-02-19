#!/usr/bin/env python3
"""Filter trufflehog JSON report to remove findings under allowlisted paths.

This script is resilient to minor variations in trufflehog output format.
"""
import json
import os
import sys
from pathlib import Path

# Allowlist may include local/private paths. To avoid hardcoding local-only
# development directories in the repository, this script reads an optional
# environment variable `TRUFFLEHOG_ALLOWLIST` containing comma-separated
# prefixes (e.g. "local_only/,tools/"). If not set, default to `tools/` only.
env_allow = os.environ.get("TRUFFLEHOG_ALLOWLIST", "")
if env_allow:
    ALLOWLIST = tuple(x.strip() for x in env_allow.split(",") if x.strip())
else:
    ALLOWLIST = ("tools/",)


def extract_path(item):
    """Best-effort extraction of a filepath from a trufflehog finding."""
    # Try common keys where filepath might appear
    for key in ("path", "file", "File", "source", "Source"):
        v = item.get(key)
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            # nested source.path
            if "path" in v:
                return v["path"]
    # Try commit/metadata fields
    for key in ("commit", "metadata"):
        v = item.get(key)
        if isinstance(v, dict) and "filename" in v:
            return v["filename"]
    return None


def allowed(path: str) -> bool:
    """Return True when `path` is under an allowlisted prefix."""
    if not path:
        return False
    p = path.replace("\\", "/")
    for a in ALLOWLIST:
        if p.startswith(a) or f"/{a}" in p:
            return True
    return False


def main(argv):
    """Filter findings from input JSON and write filtered JSON output."""
    if len(argv) < 2:
        print("Usage: filter_trufflehog_report.py input.json output.json")
        return 2
    inp = Path(argv[0])
    out = Path(argv[1])
    if not inp.exists():
        print(f"Input file {inp} not found")
        return 2
    try:
        data = json.loads(inp.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Error reading JSON: {exc}")
        return 2

    # trufflehog may emit a list of findings or an object with 'findings'
    findings = data
    if isinstance(data, dict) and "findings" in data:
        findings = data["findings"]
    if not isinstance(findings, list):
        findings = [findings]

    filtered = []
    for f in findings:
        fp = extract_path(f)
        if not allowed(fp):
            filtered.append(f)

    out.write_text(json.dumps(filtered, indent=2), encoding="utf-8")
    print(f"Wrote {len(filtered)} findings to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
