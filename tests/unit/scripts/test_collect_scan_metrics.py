import json

import scripts.collect_scan_metrics as cm


def test_collect_counts(tmp_path):
    truffle = tmp_path / "tr.json"
    sqlite = tmp_path / "sqlite.txt"
    out = tmp_path / "out.json"

    truffle.write_text(json.dumps([{"path": "a"}, {"path": "b"}]), encoding="utf-8")
    sqlite.write_text("- file1\n- file2\n", encoding="utf-8")

    rc = cm.main([str(truffle), str(sqlite), str(out)])
    assert rc == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["sqlite_findings"] == 2
    assert data["trufflehog_findings"] == 2
