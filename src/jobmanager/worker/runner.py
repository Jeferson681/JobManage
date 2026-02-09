import os
import sqlite3
from typing import Optional

from ..logging import log_event
from ..storage.core import reserve_next, update_job

DB_PATH = os.getenv("JOBMANAGER_DB", ":memory:")


def get_conn():
    """Return a sqlite3 connection using the package-level `DB_PATH`.

    Tests can override `worker.DB_PATH` to point the worker to a test DB.
    """
    # Resolve DB path from package-level attribute if present so tests can override it
    import importlib

    pkg = importlib.import_module(__package__)
    pkg_db = getattr(pkg, "DB_PATH", None)
    mod_db = globals().get("DB_PATH", DB_PATH)
    db_path = pkg_db if pkg_db and pkg_db != ":memory:" else mod_db
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
        try:
            log_event("job.succeeded", job_id=job_id, worker_id=worker_id)
        except Exception as exc:
            import logging

            logging.exception("log_event failed: %s", exc)
        return job_id
    except Exception as exc:
        update_job(conn, job_id, status="FAILED_RETRYABLE", last_error={"message": str(exc)})
        try:
            log_event("job.failed", job_id=job_id, worker_id=worker_id, error=str(exc))
        except Exception as log_exc:
            import logging

            logging.exception("log_event failed: %s", log_exc)
        return job_id


if __name__ == "__main__":
    print("Running one worker iteration")
    print(run_once())
