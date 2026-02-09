import os
import tempfile

from fastapi.testclient import TestClient

from jobmanager.api.app import app


def test_create_and_get_job():
    # use a temporary file DB so multiple connections see the same data
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        # point the package-level DB_PATH to the temp file used by handlers
        from jobmanager import api as api_mod

        api_mod.DB_PATH = path

        client = TestClient(app)

        payload = {"foo": "bar"}
        resp = client.post("/jobs", json={"job_type": "test", "payload": payload})
        assert resp.status_code == 200
        body = resp.json()
        assert "job_id" in body
        job_id = body["job_id"]

        # now fetch the job
        resp = client.get(f"/jobs/{job_id}")
        assert resp.status_code == 200
        job = resp.json()
        assert job["job_id"] == job_id
        assert job["payload"] == payload
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass
