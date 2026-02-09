import importlib

import jobmanager.worker as worker_pkg
from jobmanager.schemas import JobCreate

api_app = importlib.import_module("jobmanager.api.app")


def _boom(*_a, **_k):
    raise Exception("boom")


def test_create_job_handles_log_event_exceptions(monkeypatch):
    monkeypatch.setattr("jobmanager.logging.log_event", _boom)
    res = api_app.create_job(JobCreate(job_type="t", payload={}, max_attempts=1), idempotency_key=None)
    assert isinstance(res, dict)
    assert "job_id" in res
    assert res["status"] == "QUEUED"


def test_run_once_handles_log_event_exceptions(monkeypatch, tmp_path):
    monkeypatch.setattr("jobmanager.logging.log_event", _boom)
    db_file = tmp_path / "db.sqlite"
    # point both modules at the same DB file (set package-level worker DB_PATH)
    api_app.DB_PATH = str(db_file)
    # ensure the runner module sees the same DB path
    runner_mod = importlib.import_module("jobmanager.worker.runner")
    runner_mod.DB_PATH = str(db_file)

    # create a job directly in the DB file to ensure reservation sees it

    from jobmanager.storage.core import create_job, init_db

    # use the runner's connection helper so we create the job in the same DB
    conn = runner_mod.get_conn()
    init_db(conn)
    job_id = create_job(conn, "t", {}, 1, None)
    conn.close()

    processed = worker_pkg.run_once("w1")
    assert processed == job_id
