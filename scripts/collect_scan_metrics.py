import json
from pathlib import Path
from typing import Sequence


def main(argv: Sequence[str]) -> int:
    """Collect basic counts from trufflehog JSON and sqlite findings text.

    Expects: main([truffle_json, sqlite_txt, out_json])
    Writes a JSON file with keys `sqlite_findings` and `trufflehog_findings`.
    """
    truffle_fp = Path(argv[0])
    sqlite_fp = Path(argv[1])
    out_fp = Path(argv[2])

    truffle_list = json.loads(truffle_fp.read_text(encoding="utf-8")) if truffle_fp.exists() else []
    sqlite_text = sqlite_fp.read_text(encoding="utf-8") if sqlite_fp.exists() else ""

    sqlite_count = sum(1 for line in sqlite_text.splitlines() if line.strip().startswith("-"))
    truffle_count = len(truffle_list)

    out_fp.write_text(json.dumps({"sqlite_findings": sqlite_count, "trufflehog_findings": truffle_count}), encoding="utf-8")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
