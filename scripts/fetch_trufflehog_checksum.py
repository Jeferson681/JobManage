import hashlib
from pathlib import Path
from typing import Optional

try:
    from urllib.request import urlopen
except Exception:  # pragma: no cover - fallback for environments
    urlopen = None  # type: ignore


def fetch_and_write(version: str, url: Optional[str] = None) -> int:
    """Fetch a release artifact and write its SHA256 into tools/trufflehog.sha256.

    Tests monkeypatch `urlopen` so a simple implementation is sufficient.
    """
    if url is None:
        url = f"https://example.com/trufflehog/{version}/trufflehog.bin"
    resp = urlopen(url)
    data = resp.read()
    digest = hashlib.sha256(data).hexdigest()
    out_dir = Path("tools")
    out_dir.mkdir(parents=True, exist_ok=True)
    fp = out_dir / "trufflehog.sha256"
    fp.write_text(digest, encoding="utf-8")
    return 0


if __name__ == "__main__":
    import sys

    rc = fetch_and_write(sys.argv[1] if len(sys.argv) > 1 else "")
    raise SystemExit(rc)
