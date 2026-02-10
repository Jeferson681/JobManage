import sqlite3
from datetime import datetime, timedelta, timezone

from jobmanager.storage import core as storage


def test_two_workers_cannot_reserve_same_job(tmp_path):
    db_path = str(tmp_path / "test_concurrency.db")

    # create initial DB and a queued job
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    storage.init_db(conn)
    job_id = storage.create_job(conn, "task", {"x": 1}, max_attempts=3)
    conn.close()

    # open two independent connections simulating two workers
    c1 = sqlite3.connect(db_path, check_same_thread=False)
    c1.row_factory = sqlite3.Row
    c2 = sqlite3.connect(db_path, check_same_thread=False)
    c2.row_factory = sqlite3.Row

    # worker1 reserves the job
    j1 = storage.reserve_next(c1, "worker-1", lease_seconds=30)
    assert j1 is not None
    assert j1["job_id"] == job_id
    assert j1["status"] == "RUNNING"
    assert j1["worker_id"] == "worker-1"

    # worker2 should not be able to reserve the same job while locked
    j2 = storage.reserve_next(c2, "worker-2", lease_seconds=30)
    assert j2 is None

    # simulate the worker crashing: set status back to QUEUED and expire lock
    past = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    storage.update_job(c1, job_id, status="QUEUED")
    storage.update_job(c1, job_id, locked_until=past)

    # now worker2 can reserve (attempt will increment)
    j3 = storage.reserve_next(c2, "worker-2", lease_seconds=30)
    assert j3 is not None
    assert j3["worker_id"] == "worker-2"

    c1.close()
    c2.close()
