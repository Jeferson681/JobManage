import os
import tempfile

from jobmanager.storage.core import create_job, get_job, init_db
from jobmanager.worker.runner import run_once


def test_worker_runs_job():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        # initialize DB and create a job
        import sqlite3

        conn = sqlite3.connect(path, check_same_thread=False)
        init_db(conn)
        job_id = create_job(conn, "test", {"x": 1}, max_attempts=1)
        conn.close()

        # point worker to same DB and run one iteration
        from jobmanager import worker as worker_mod

        worker_mod.DB_PATH = path
        processed = run_once(worker_id="test-worker")
        assert processed == job_id

        # verify job status was updated
        conn = sqlite3.connect(path, check_same_thread=False)
        job = get_job(conn, job_id)
        assert job["status"] == "SUCCEEDED"
        conn.close()
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass
