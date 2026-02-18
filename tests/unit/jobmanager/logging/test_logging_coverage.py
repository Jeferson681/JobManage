import importlib
import sqlite3

from jobmanager.logging import log_event


def test_log_event_fallback(monkeypatch):
    # make json.dumps raise to exercise the fallback path
    import jobmanager.logging as logging_mod

    def _bad(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(logging_mod.json, "dumps", _bad)
    # should not raise
    log_event("event.test", foo="bar")


def test_storage_update_status_logs(monkeypatch):
    recorded = []

    def recorder(event, **fields):
        recorded.append((event, fields.copy()))

    monkeypatch.setattr("jobmanager.logging.log_event", recorder)
    monkeypatch.setattr("jobmanager.storage.core.log_event", recorder)

    from jobmanager.storage.core import create_job, init_db, update_job

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    init_db(conn)
    job_id = create_job(conn, "t", {"a": 1})
    update_job(conn, job_id, status="SUCCEEDED")

    assert any(evt == "job.status_changed" for evt, _ in recorded)


def test_reserve_next_logs(monkeypatch):
    recorded = []

    def recorder(event, **fields):
        recorded.append((event, fields.copy()))

    monkeypatch.setattr("jobmanager.logging.log_event", recorder)
    monkeypatch.setattr("jobmanager.storage.core.log_event", recorder)

    from jobmanager.storage.core import create_job, init_db, reserve_next

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    init_db(conn)
    create_job(conn, "t", {"x": 1})
    job = reserve_next(conn, "w-1", lease_seconds=5)
    assert job is not None
    assert any(evt == "job.reserved" for evt, _ in recorded)


def test_worker_run_once_logs(monkeypatch, tmp_path):
    recorded = []

    def recorder(event, **fields):
        recorded.append((event, fields.copy()))

    monkeypatch.setattr("jobmanager.logging.log_event", recorder)
    monkeypatch.setattr("jobmanager.storage.core.log_event", recorder)
    monkeypatch.setattr("jobmanager.worker.runner.log_event", recorder)

    db_file = tmp_path / "w.db"
    runner_mod = importlib.import_module("jobmanager.worker.runner")
    runner_mod.DB_PATH = str(db_file)

    conn = runner_mod.get_conn()
    from jobmanager.storage.core import create_job, init_db

    init_db(conn)
    job_id = create_job(conn, "t", {"y": 2})
    conn.close()

    processed = runner_mod.run_once("w-9")
    assert processed == job_id
    assert any(evt == "job.succeeded" for evt, _ in recorded)


def test_worker_run_once_handles_processing_exception(monkeypatch, tmp_path):
    # simulate an error during processing so the outer except path runs
    recorded = []

    def recorder(event, **fields):
        recorded.append((event, fields.copy()))

    monkeypatch.setattr("jobmanager.logging.log_event", recorder)
    monkeypatch.setattr("jobmanager.storage.core.log_event", recorder)
    monkeypatch.setattr("jobmanager.worker.runner.log_event", recorder)

    import importlib

    runner_mod = importlib.import_module("jobmanager.worker.runner")
    runner_mod.DB_PATH = str(tmp_path / "fail.db")

    from jobmanager.storage import core as storage_core

    conn = runner_mod.get_conn()
    from jobmanager.storage.core import create_job, get_job, init_db

    init_db(conn)
    job_id = create_job(conn, "t", {"y": 2})
    conn.close()

    # wrap the real update_job to raise on the SUCCEEDED transition only
    real_update = storage_core.update_job

    def update_maybe_raise(conn, jid, **fields):
        if fields.get("status") == "SUCCEEDED":
            raise RuntimeError("processing failed")
        return real_update(conn, jid, **fields)

    monkeypatch.setattr("jobmanager.storage.core.update_job", update_maybe_raise)
    # runner module imported `update_job` at import time; patch that reference too
    monkeypatch.setattr("jobmanager.worker.runner.update_job", update_maybe_raise)

    processed = runner_mod.run_once("w-fail")
    assert processed == job_id

    # the worker should have attempted to mark the job failed
    conn2 = runner_mod.get_conn()
    j = get_job(conn2, job_id)
    assert j is not None and j["status"] == "FAILED_RETRYABLE"
    assert any(evt == "job.failed" for evt, _ in recorded)


def test_update_job_handles_various_field_types():
    from jobmanager.storage.core import create_job, find_by_idempotency_key, get_job, init_db, update_job

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    init_db(conn)
    job_id = create_job(conn, "t", {"a": 1}, idempotency_key="k1")

    # update result with a dict (should be JSON-encoded)
    update_job(conn, job_id, result={"ok": True})
    # update last_error with a dict
    update_job(conn, job_id, last_error={"err": "x"})
    # update payload
    update_job(conn, job_id, payload={"new": 1})

    j = get_job(conn, job_id)
    assert j is not None
    assert isinstance(j.get("result"), dict)
    assert isinstance(j.get("last_error"), dict)
    assert isinstance(j.get("payload"), dict)

    # find by idempotency key
    assert find_by_idempotency_key(conn, "k1") == job_id
