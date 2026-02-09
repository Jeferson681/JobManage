import os
import sqlite3
import tempfile

from jobmanager.storage.core import create_job, get_job, init_db
from jobmanager.worker.runner import run_once


def test_run_once_honors_cancel_request(tmp_path, monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        # init db and create job
        conn = sqlite3.connect(path, check_same_thread=False)
        init_db(conn)
        jid = create_job(conn, "t", {"a": 1}, max_attempts=2)
        conn.close()

        # make the package-level worker point to the DB
        from jobmanager import worker as worker_pkg

        worker_pkg.DB_PATH = path

        # Monkeypatch reserve_next to return the job as if it were reserved
        def fake_reserve(conn, worker_id, lease_seconds=10):
            # simulate the reservation incrementing attempt
            cur = conn.cursor()
            cur.execute(
                "UPDATE jobs SET status='RUNNING', worker_id=?, attempt=attempt+1 WHERE job_id=?", (worker_id, jid)
            )
            conn.commit()
            from jobmanager.storage.core import get_job

            return get_job(conn, jid)

        monkeypatch.setattr("jobmanager.worker.runner.reserve_next", fake_reserve)

        # Monkeypatch get_job to simulate that the job was marked CANCEL_REQUESTED
        def fake_get_job(conn, job_id):
            return {"job_id": job_id, "status": "CANCEL_REQUESTED"}

        monkeypatch.setattr("jobmanager.storage.core.get_job", fake_get_job)

        processed = run_once(worker_id="w-cancel")
        assert processed == jid

        # verify job is canceled in DB
        conn2 = sqlite3.connect(path, check_same_thread=False)
        job = get_job(conn2, jid)
        assert job["status"] == "CANCELED"
        conn2.close()
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def test_run_once_marks_failed_final_when_attempts_exhausted(tmp_path, monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        conn = sqlite3.connect(path, check_same_thread=False)
        init_db(conn)
        # create job with max_attempts=1 so first exception exhausts attempts
        jid = create_job(conn, "t", {"a": 1}, max_attempts=1)
        conn.close()

        from jobmanager import worker as worker_pkg

        worker_pkg.DB_PATH = path

        # Make update_job raise only when attempting to mark SUCCEEDED
        import jobmanager.storage.core as storage_core

        real_update = storage_core.update_job

        def flaky_update(conn, job_id, **fields):
            if fields.get("status") == "SUCCEEDED":
                raise RuntimeError("simulate processing error")
            return real_update(conn, job_id, **fields)

        # Patch the runner's update_job reference so run_once observes the flaky behavior
        monkeypatch.setattr("jobmanager.worker.runner.update_job", flaky_update)

        processed = run_once(worker_id="w-final")
        assert processed == jid

        # verify job marked FAILED_FINAL
        conn2 = sqlite3.connect(path, check_same_thread=False)
        job = get_job(conn2, jid)
        assert job["status"] == "FAILED_FINAL"
        conn2.close()
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def test_run_once_schedules_retryable_with_jitter(tmp_path, monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        conn = sqlite3.connect(path, check_same_thread=False)
        init_db(conn)
        # create job with max_attempts > 1 so retryable path is used
        jid = create_job(conn, "t", {"a": 1}, max_attempts=3)
        conn.close()

        from jobmanager import worker as worker_pkg

        worker_pkg.DB_PATH = path

        import jobmanager.storage.core as storage_core

        real_update = storage_core.update_job

        def flaky_update(conn, job_id, **fields):
            if fields.get("status") == "SUCCEEDED":
                raise RuntimeError("simulate processing error")
            return real_update(conn, job_id, **fields)

        monkeypatch.setattr("jobmanager.worker.runner.update_job", flaky_update)
        # deterministic jitter
        monkeypatch.setattr("random.uniform", lambda a, b: 5.0)

        processed = run_once(worker_id="w-retry")
        assert processed == jid

        # verify job marked FAILED_RETRYABLE and next_run_at set
        conn2 = sqlite3.connect(path, check_same_thread=False)
        job = get_job(conn2, jid)
        assert job["status"] == "FAILED_RETRYABLE"
        assert job["next_run_at"] is not None
        conn2.close()
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def test_run_loop_exits_after_max_iterations(tmp_path):
    # ensure the run loop executes and exits cleanly when no jobs available
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        conn = sqlite3.connect(path, check_same_thread=False)
        init_db(conn)
        conn.close()

        from jobmanager import worker as worker_pkg

        worker_pkg.DB_PATH = path

        # run loop with zero poll interval and max_iterations=2
        from jobmanager.worker.runner import run

        run(worker_id="loop-test", poll_interval=0.0, max_iterations=2)
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass
