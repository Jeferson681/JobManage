import random
from datetime import datetime, timezone

from jobmanager.storage.core import create_job, get_job, init_db
from jobmanager.worker import runner as runner_mod


def test_full_jitter_applied(monkeypatch, tmp_path):
    db = tmp_path / "j.db"
    runner_mod.DB_PATH = str(db)
    conn = runner_mod.get_conn()
    init_db(conn)
    jid = create_job(conn, "t", {"a": 1}, max_attempts=2)
    conn.close()

    # force the worker to hit the exception path by making update_job raise
    import importlib

    storage_core = importlib.import_module("jobmanager.storage.core")

    real_update = storage_core.update_job

    def raise_on_succeeded(conn, job_id, **fields):
        if fields.get("status") == "SUCCEEDED":
            raise RuntimeError("boom")
        return real_update(conn, job_id, **fields)

    monkeypatch.setattr(storage_core, "update_job", raise_on_succeeded)
    # runner module imported update_job at import-time; patch that reference too
    monkeypatch.setattr("jobmanager.worker.runner.update_job", raise_on_succeeded)

    # monkeypatch random.uniform to return a deterministic delay (e.g., 7.5s)
    monkeypatch.setattr(random, "uniform", lambda a, b: 7.5)

    # run the worker iteration which will schedule a retry with jitter
    processed = runner_mod.run_once("w-jitter")
    assert processed == jid

    conn2 = runner_mod.get_conn()
    j = get_job(conn2, jid)
    assert j is not None and j["status"] == "FAILED_RETRYABLE"
    # next_run_at should be approximately now + 7.5s
    next_run = datetime.fromisoformat(j["next_run_at"])
    delta = (next_run - datetime.now(timezone.utc)).total_seconds()
    assert 6.0 <= delta <= 9.0
