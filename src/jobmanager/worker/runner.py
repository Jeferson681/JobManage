import os
import sqlite3
from typing import Optional

from ..storage.core import reserve_next, update_job

DB_PATH = os.getenv("JOBMANAGER_DB", ":memory:")


def get_conn():
    """Return a sqlite3 connection using the package-level `DB_PATH`.

    Tests can override `worker.DB_PATH` to point the worker to a test DB.
    """
    # Resolve DB path from package-level attribute if present so tests can override it
    import importlib

    pkg = importlib.import_module(__package__)
    db_path = getattr(pkg, "DB_PATH", DB_PATH)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def run_once(worker_id: str = "worker-1") -> Optional[str]:
    """Run a single worker iteration: reserve a job and process it once.

    Returns the `job_id` of the processed job or `None` if no job was available.
    The current scaffold simulates successful work by immediately marking the
    job as `SUCCEEDED`.
    """
    conn = get_conn()
    job = reserve_next(conn, worker_id, lease_seconds=10)
    if not job:
        return None
    job_id = job["job_id"]
    try:
        # Simulate work: here we just succeed immediately.
        result = {"message": "ok"}
        update_job(conn, job_id, status="SUCCEEDED", result=result, locked_until=None, worker_id=None)
        return job_id
    except Exception as exc:
        update_job(conn, job_id, status="FAILED_RETRYABLE", last_error={"message": str(exc)})
        return job_id


if __name__ == "__main__":
    print("Running one worker iteration")
    print(run_once())
