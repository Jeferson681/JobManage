from pathlib import Path


def main(paths) -> int:
    """Return 1 if any file outside `scripts/` contains sqlite3.connect usage.

    The checker is intentionally minimal: tests place a temporary file
    outside `scripts/` and expect detection (rc=1). Files under `scripts/`
    are considered allow-listed.
    """
    for p in paths:
        path = Path(p)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "sqlite3.connect" in text:
            if not str(path).startswith("scripts/"):
                return 1
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
