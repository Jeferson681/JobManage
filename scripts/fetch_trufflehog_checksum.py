#!/usr/bin/env python3
"""Fetch trufflehog release tarball and write SHA256 checksum to tools/trufflehog.sha256.

Usage: python scripts/fetch_trufflehog_checksum.py <version>
Example: python scripts/fetch_trufflehog_checksum.py 3.0.1
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from urllib.request import urlopen


def fetch_and_write(version: str) -> int:
    """Download the tarball for `version`, compute SHA256 and write to tools/trufflehog.sha256.

    Returns 0 on success, non-zero on error.
    """
    url = f"https://github.com/trufflesecurity/trufflehog/releases/download/v{version}/trufflehog_{version}_linux_amd64.tar.gz"
    print(f"Downloading {url}... (only to compute checksum)")
    try:
        with urlopen(url) as resp:
            data = resp.read()
    except Exception as exc:
        print("Failed to download:", exc)
        return 2
    sha = hashlib.sha256(data).hexdigest()
    outp = Path("tools")
    outp.mkdir(parents=True, exist_ok=True)
    fp = outp / "trufflehog.sha256"
    fp.write_text(sha + "\n", encoding="utf-8")
    print(f"Wrote checksum to {fp}: {sha}")
    return 0


def main(argv: list[str]) -> int:
    """CLI entrypoint.

    Expects a single argument: the trufflehog release version (e.g., '3.0.1').
    """
    if len(argv) != 1:
        print("Usage: fetch_trufflehog_checksum.py <version>")
        return 2
    return fetch_and_write(argv[0])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
