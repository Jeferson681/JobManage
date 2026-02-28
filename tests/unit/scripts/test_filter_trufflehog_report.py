import importlib
import json


def test_filter_removes_allowlisted_paths(tmp_path, monkeypatch):
    inp = tmp_path / "in.json"
    out = tmp_path / "out.json"
    # findings: one allowlisted under local/private, one regular
    findings = [
        {"path": "local_only/secret.txt", "match": "KEY"},
        {"path": "src/jobmanager/config.py", "match": "PASSWORD"},
    ]
    inp.write_text(json.dumps(findings), encoding="utf-8")

    # ensure allowlist excludes private paths by setting env variable
    monkeypatch.setenv("TRUFFLEHOG_ALLOWLIST", "local_only/,tools/")
    # import module after setting env so it picks up ALLOWLIST at import time
    flt = importlib.import_module("scripts.filter_trufflehog_report")

    rc = flt.main([str(inp), str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    # only the non-allowlisted finding should remain
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["path"] == "src/jobmanager/config.py"
