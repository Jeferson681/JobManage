import json
import sqlite3
from pathlib import Path


def test_generate_artifacts(tmp_path):
    """Unit test for private_docs/tools/generate_artifacts.generate()

    Creates a temporary sqlite DB, seeds a few jobs, calls the generator
    and asserts `metrics.txt` and `health.txt` contain expected structure.
    """
    db_path = tmp_path / "demo.db"
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    # create DB and seed jobs using the project's storage helpers
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    from jobmanager.storage.core import create_job, init_db, update_job

    init_db(conn)
    j1 = create_job(conn, "t-success", {"x": 1}, max_attempts=1)
    j2 = create_job(conn, "t-cancel", {"x": 2}, max_attempts=1)

    # set explicit statuses for deterministic metrics
    update_job(conn, j1, status="SUCCEEDED")
    update_job(conn, j2, status="CANCELED")
    conn.close()

    # import generator by running the script (keeps tests free of package-layout assumptions)
    import runpy

    mod = runpy.run_path(str(Path("private_docs") / "tools" / "generate_artifacts.py"))
    gen = mod["generate"]
    gen(str(db_path), str(out_dir))

    metrics_path = out_dir / "metrics.txt"
    health_path = out_dir / "health.txt"

    assert metrics_path.exists(), "metrics.txt not generated"
    assert health_path.exists(), "health.txt not generated"

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    health = json.loads(health_path.read_text(encoding="utf-8"))

    assert health.get("status") == "ok"

    jobs_by_status = metrics.get("jobs_by_status") or {}
    assert int(jobs_by_status.get("SUCCEEDED", 0)) >= 1
    assert int(jobs_by_status.get("CANCELED", 0)) >= 1
