import sqlite3

from jobmanager.storage import create_job, get_job, init_db, reserve_next


def test_create_job_persists_fields():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    payload = {"x": 1}
    job_id = create_job(conn, "noop", payload, max_attempts=5, idempotency_key="abc")

    job = get_job(conn, job_id)
    assert job is not None
    assert job["job_type"] == "noop"
    assert job["payload"] == payload
    assert job["max_attempts"] == 5
    assert job["idempotency_key"] == "abc"
    assert job["status"] == "QUEUED"


def test_reserve_next_sets_running_and_locks():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    job_id = create_job(conn, "noop", {"k": "v"})
    reserved = reserve_next(conn, "worker-a", lease_seconds=60)
    assert reserved is not None
    assert reserved["job_id"] == job_id
    assert reserved["status"] == "RUNNING"

    # second reserve should not find the same job because it's locked
    reserved2 = reserve_next(conn, "worker-b", lease_seconds=60)
    assert reserved2 is None
