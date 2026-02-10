import sqlite3

from fastapi.testclient import TestClient

from jobmanager import api


def make_payload():
    return {"job_type": "email", "payload": {"to": "user@example.com"}, "max_attempts": 2}


def test_create_job_idempotent(tmp_path):
    db_path = str(tmp_path / "test_idem.db")
    # Override the package-level DB path used by the API
    api.DB_PATH = db_path

    client = TestClient(api.app)

    headers = {"Idempotency-Key": "idem-123"}
    resp1 = client.post("/jobs", json=make_payload(), headers=headers)
    assert resp1.status_code in (200, 201)
    j1 = resp1.json()
    assert "job_id" in j1

    resp2 = client.post("/jobs", json=make_payload(), headers=headers)
    # The second call with the same Idempotency-Key should return 200
    assert resp2.status_code == 200
    j2 = resp2.json()
    assert j1["job_id"] == j2["job_id"]

    # Verify only one job row exists in the DB
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs")
    count = cur.fetchone()[0]
    conn.close()
    assert count == 1
