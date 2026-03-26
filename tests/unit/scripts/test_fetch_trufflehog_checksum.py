import hashlib
import os
import sys
from pathlib import Path

# Ensure repo root is first on sys.path so `import scripts.*` resolves here
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

import scripts.fetch_trufflehog_checksum as fc


def test_fetch_and_write(tmp_path, monkeypatch):
    data = b"hello world"

    class DummyResp:
        def __init__(self, data):
            self._data = data

        def read(self):
            return self._data

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(fc, "urlopen", lambda url: DummyResp(data))
    # write output into temporary cwd to avoid touching repo tools/
    monkeypatch.chdir(tmp_path)

    rc = fc.fetch_and_write("1.2.3")
    assert rc == 0
    fp = Path("tools") / "trufflehog.sha256"
    assert fp.exists()
    assert fp.read_text(encoding="utf-8").strip() == hashlib.sha256(data).hexdigest()
