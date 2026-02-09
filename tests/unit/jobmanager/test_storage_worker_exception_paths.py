import importlib
import sqlite3


def _boom(*_a, **_k):
    raise Exception("boom")


def test_create_job_storage_log_exception(monkeypatch):
    from jobmanager.storage import core as storage_core

    monkeypatch.setattr(storage_core, "log_event", _boom)

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    storage_core.init_db(conn)
    # should not raise despite log_event raising
    jid = storage_core.create_job(conn, "t", {"a": 1})
    assert jid is not None


def test_reserve_next_storage_log_exception(monkeypatch):
    from jobmanager.storage import core as storage_core

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    storage_core.init_db(conn)
    storage_core.create_job(conn, "t", {"a": 1})

    monkeypatch.setattr(storage_core, "log_event", _boom)
    # should return a job even if logging raises
    job = storage_core.reserve_next(conn, "w-1", lease_seconds=5)
    assert job is not None


def test_update_job_status_log_exception(monkeypatch):
    from jobmanager.storage import core as storage_core

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    storage_core.init_db(conn)
    jid = storage_core.create_job(conn, "t", {"a": 1})

    monkeypatch.setattr(storage_core, "log_event", _boom)
    # should not raise when status-change logging errors
    storage_core.update_job(conn, jid, status="SUCCEEDED")
    j = storage_core.get_job(conn, jid)
    assert j is not None and j["status"] == "SUCCEEDED"


def test_worker_log_event_exception_paths(monkeypatch, tmp_path):
    runner_mod = importlib.import_module("jobmanager.worker.runner")
    storage_core = importlib.import_module("jobmanager.storage.core")

    # point runner to a real file DB
    db_file = tmp_path / "wex.db"
    runner_mod.DB_PATH = str(db_file)

    conn = runner_mod.get_conn()
    storage_core.init_db(conn)
    jid = storage_core.create_job(conn, "t", {"x": 1})
    conn.close()

    # case 1: log_event raises on success path
    monkeypatch.setattr(runner_mod, "log_event", _boom)
    # should still process and return job id
    processed = runner_mod.run_once("w-1")
    assert processed == jid

    # case 2: force processing to fail and log_event raise in failure path
    # make update_job raise during SUCCEEDED to force outer except
    real_update = storage_core.update_job

    def raise_on_succeeded(conn, job_id, **fields):
        if fields.get("status") == "SUCCEEDED":
            raise RuntimeError("fail")
        return real_update(conn, job_id, **fields)

    monkeypatch.setattr(storage_core, "update_job", raise_on_succeeded)
    monkeypatch.setattr(runner_mod, "log_event", _boom)

    # create another job
    conn2 = runner_mod.get_conn()
    jid2 = storage_core.create_job(conn2, "t", {"y": 2})
    conn2.close()

    processed2 = runner_mod.run_once("w-2")
    assert processed2 == jid2
