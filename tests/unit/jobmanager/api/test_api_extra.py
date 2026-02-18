import os
import tempfile

from fastapi.testclient import TestClient

from jobmanager.api.app import app


def test_idempotency_prevents_duplicate_creation():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        from jobmanager import api as api_mod

        api_mod.DB_PATH = path
        client = TestClient(app)

        payload = {"n": 1}
        headers = {"Idempotency-Key": "my-key"}
        r1 = client.post("/jobs", json={"job_type": "t", "payload": payload}, headers=headers)
        assert r1.status_code == 200
        body1 = r1.json()

        r2 = client.post("/jobs", json={"job_type": "t", "payload": payload}, headers=headers)
        assert r2.status_code == 200
        body2 = r2.json()

        # the second call with same idempotency key should return the same job id
        assert body1["job_id"] == body2["job_id"]
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def test_cancel_endpoint_marks_cancel_requested():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        import sqlite3

        conn = sqlite3.connect(path, check_same_thread=False)
        from jobmanager.storage.core import create_job, init_db

        init_db(conn)
        job_id = create_job(conn, "t", {"a": 1})
        conn.close()

        from jobmanager import api as api_mod

        api_mod.DB_PATH = path
        client = TestClient(app)

        resp = client.post(f"/jobs/{job_id}/cancel")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "CANCEL_REQUESTED"

        # verify persisted
        conn = sqlite3.connect(path, check_same_thread=False)
        from jobmanager.storage.core import get_job

        job = get_job(conn, job_id)
        assert job["status"] == "CANCEL_REQUESTED"
        conn.close()
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def test_get_job_404_for_missing():
    from jobmanager import api as api_mod

    api_mod.DB_PATH = ":memory:"
    client = TestClient(app)
    resp = client.get("/jobs/not-a-job")
    assert resp.status_code == 404
