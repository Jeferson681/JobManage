import sqlite3
import tempfile

from fastapi.testclient import TestClient

from jobmanager import api
from jobmanager.storage.core import get_job, init_db


def test_api_enqueue_and_worker_processes_job():
    fd, path = tempfile.mkstemp(suffix=".db")
    try:
        # ensure DB and API point to same file
        conn = sqlite3.connect(path, check_same_thread=False)
        init_db(conn)
        conn.close()

        api.DB_PATH = path
        client = TestClient(api.app)

        payload = {"job_type": "e2e", "payload": {"x": 1}, "max_attempts": 2}
        resp = client.post("/jobs", json=payload)
        assert resp.status_code in (200, 201)
        body = resp.json()
        jid = body["job_id"]

        # point the worker to the same DB and run a single iteration
        from jobmanager.worker import runner as runner_mod

        runner_mod.DB_PATH = path
        processed = runner_mod.run_once("e2e-worker")
        assert processed == jid

        # verify job succeeded
        conn2 = sqlite3.connect(path, check_same_thread=False)
        job = get_job(conn2, jid)
        assert job is not None and job["status"] == "SUCCEEDED"
        conn2.close()
    finally:
        import os

        try:
            os.unlink(path)
        except Exception:
            pass
