#!/usr/bin/env python3
"""Download and vendorize a pinned trufflehog tarball into tools/ with checksum verification.

Usage: python scripts/vendor_trufflehog.py <version>
This will download the tarball, verify sha256 against tools/trufflehog.sha256,
extract the binary into tools/ and make it executable.
"""
from __future__ import annotations

import hashlib
import sys
import tarfile
from pathlib import Path
from urllib.request import urlopen


def read_expected_checksum() -> str | None:
    """Return the expected checksum string from `tools/trufflehog.sha256`, or None if not present."""
    p = Path("tools/trufflehog.sha256")
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8").strip()


def download_tarball(version: str) -> bytes | None:
    """Download the trufflehog tarball for the given `version` and return its bytes, or None on error."""
    url = f"https://github.com/trufflesecurity/trufflehog/releases/download/v{version}/trufflehog_{version}_linux_amd64.tar.gz"
    print(f"Downloading {url}")
    try:
        with urlopen(url) as resp:
            return resp.read()
    except Exception as exc:
        print("Download failed:", exc)
        return None


def verify_and_extract(data: bytes, expected: str | None) -> bool:
    """Verify SHA256 of `data` against `expected` (if provided) and extract into `tools/`.

    Returns True on success.
    """
    actual = hashlib.sha256(data).hexdigest()
    if expected and expected != actual:
        print(f"Checksum mismatch: expected {expected} != actual {actual}")
        return False
    # write to temp file and extract
    tmp = Path("/tmp") / "trufflehog.tar.gz"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(data)
    try:
        with tarfile.open(tmp, "r:gz") as tf:
            tf.extractall(path="tools")
    except Exception as exc:
        print("Extraction failed:", exc)
        return False
    # ensure binary is executable
    binpath = Path("tools") / "trufflehog"
    if binpath.exists():
        try:
            binpath.chmod(0o755)
        except Exception:
            pass
    print("Vendored trufflehog to tools/")
    return True


def main(argv: list[str]) -> int:
    """CLI entrypoint: vendor a trufflehog release into tools/.

    Expects one arg: the release version (e.g., '3.0.1').
    """
    if len(argv) != 1:
        print("Usage: vendor_trufflehog.py <version>")
        return 2
    version = argv[0]
    expected = read_expected_checksum()
    data = download_tarball(version)
    if data is None:
        return 3
    ok = verify_and_extract(data, expected)
    return 0 if ok else 4


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
