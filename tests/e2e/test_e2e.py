import sqlite3

from fastapi.testclient import TestClient

from jobmanager import api, storage, worker


def test_create_and_process_job(tmp_path):
    db_file = tmp_path / "test.db"
    api.DB_PATH = str(db_file)
    worker.DB_PATH = str(db_file)

    # ensure DB and app startup
    conn = sqlite3.connect(api.DB_PATH)
    conn.row_factory = sqlite3.Row
    storage.init_db(conn)
    conn.close()

    client = TestClient(api.app)

    # create job
    payload = {"hello": "world"}
    r = client.post("/jobs", json={"job_type": "noop", "payload": payload})
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    # process one job with worker
    processed = worker.run_once(worker_id="test-worker")
    assert processed == job_id

    # check final state
    r2 = client.get(f"/jobs/{job_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "SUCCEEDED"
