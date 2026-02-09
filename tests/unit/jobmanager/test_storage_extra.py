import sqlite3

from jobmanager.storage.core import create_job, find_by_idempotency_key, get_job, init_db, update_job


def test_update_job_fields_and_json_decoding():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    job_id = create_job(conn, "t", {"x": 1})

    # update result and last_error as dicts and ensure get_job decodes them
    update_job(conn, job_id, result={"ok": True})
    update_job(conn, job_id, last_error={"msg": "oops"})

    job = get_job(conn, job_id)
    assert job["result"] == {"ok": True}
    assert job["last_error"] == {"msg": "oops"}


def test_find_by_idempotency_key_returns_none_when_missing():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    assert find_by_idempotency_key(conn, "nope") is None


def test_update_payload_and_max_attempts():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    job_id = create_job(conn, "t", {"a": 1}, max_attempts=2)
    update_job(conn, job_id, payload={"a": 2})
    update_job(conn, job_id, max_attempts=5)
    job = get_job(conn, job_id)
    assert job["payload"]["a"] == 2
    assert job["max_attempts"] == 5
