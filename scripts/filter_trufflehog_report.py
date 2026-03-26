import json
import os
from pathlib import Path
from typing import Sequence


def _load_allowlist() -> list:
    raw = os.environ.get("TRUFFLEHOG_ALLOWLIST", "")
    if not raw:
        return []
    # comma separated prefixes
    return [p.strip() for p in raw.split(",") if p.strip()]


def main(argv: Sequence[str]) -> int:
    """Filter a trufflehog JSON report by removing allowlisted path prefixes.

    Usage: main([in.json, out.json])
    """
    in_fp = Path(argv[0])
    out_fp = Path(argv[1])
    allow = _load_allowlist()

    data = json.loads(in_fp.read_text(encoding="utf-8")) if in_fp.exists() else []
    filtered = []
    for item in data:
        path = item.get("path", "")
        skip = any(path.startswith(prefix) for prefix in allow)
        if not skip:
            filtered.append(item)

    out_fp.write_text(json.dumps(filtered), encoding="utf-8")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
