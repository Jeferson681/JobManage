import sqlite3

from fastapi.testclient import TestClient

from jobmanager import api, storage


def test_api_posts_job_and_gets_queued(tmp_path):
    db_file = tmp_path / "int-db.sqlite"
    api.DB_PATH = str(db_file)

    # prepare DB
    conn = sqlite3.connect(api.DB_PATH)
    conn.row_factory = sqlite3.Row
    storage.init_db(conn)
    conn.close()

    client = TestClient(api.app)

    payload = {"hello": "world"}
    r = client.post("/jobs", json={"job_type": "noop", "payload": payload})
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    r2 = client.get(f"/jobs/{job_id}")
    assert r2.status_code == 200
    data = r2.json()
    assert data["status"] == "QUEUED"
