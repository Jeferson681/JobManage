import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from ..logging import log_event
from ..schemas import JobCreate
from ..storage.core import create_job as storage_create_job
from ..storage.core import find_by_idempotency_key, get_job, init_db

DB_PATH = os.getenv("JOBMANAGER_DB", ":memory:")


def get_conn():
    """Return a sqlite3 connection using the package-level `DB_PATH`.

    Tests may override `api.DB_PATH` before calling handlers; this function
    reads the package attribute at runtime to respect such overrides.
    """
    # Prefer a `DB_PATH` set on the parent package (jobmanager.api) so tests
    # that do `from jobmanager import api as api_mod; api_mod.DB_PATH = path`
    # continue to work. Fall back to this module's DB_PATH when not present.
    import importlib

    try:
        pkg = importlib.import_module(__package__)
        pkg_db = getattr(pkg, "DB_PATH", None)
        mod_db = globals().get("DB_PATH", DB_PATH)
        # Prefer a package-level override when present (typical test usage).
        # If the package is still using the default in-memory DB, allow the
        # module-level DB_PATH to take precedence (useful in some tests).
        db_path = pkg_db if pkg_db and pkg_db != ":memory:" else mod_db
    except Exception:
        db_path = globals().get("DB_PATH", DB_PATH)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Ensure the schema exists for this connection; calling init_db is
    # idempotent and safe. This guarantees tests which override
    # `DB_PATH` see the expected tables even if lifespan isn't run.
    try:
        init_db(conn)
    except sqlite3.Error:
        # If schema creation fails for this connection, allow request
        # handling to proceed so a clearer error is raised later.
        pass
    return conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler to ensure the DB schema exists at startup."""
    conn = get_conn()
    init_db(conn)
    yield


app = FastAPI(title="JobManager (dev scaffold)", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    """Liveness probe.

    Returns 200 if the process is running.
    """
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict:
    """Readiness probe.

    Returns 200 when the service can connect to the DB.
    """
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        return {"status": "ok"}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=503, detail=f"db not ready: {exc}")


@app.get("/metrics")
def metrics() -> dict:
    """Return minimal operational metrics.

    This is intentionally simple (JSON). It is good enough for local debugging
    and basic CI validation.
    """
    conn = get_conn()
    cur = conn.cursor()

    jobs_by_status: dict[str, int] = {}
    cur.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
    for status, count in cur.fetchall():
        jobs_by_status[str(status)] = int(count)

    cur.execute("SELECT COUNT(*) FROM jobs WHERE status = 'FAILED_RETRYABLE'")
    retry_jobs = int(cur.fetchone()[0])

    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'RUNNING' AND locked_until IS NOT NULL AND locked_until <= ?",
        (now_iso,),
    )
    orphaned_running = int(cur.fetchone()[0])

    return {
        "jobs_by_status": jobs_by_status,
        "retry_jobs": retry_jobs,
        "orphaned_running": orphaned_running,
    }


@app.post("/jobs")
def create_job(item: JobCreate, idempotency_key: Optional[str] = Header(None)):
    """HTTP POST /jobs handler: enqueue a new job.

    Respects an optional `Idempotency-Key` header to prevent duplicate
    job creation.
    """
    conn = get_conn()
    if idempotency_key:
        found = find_by_idempotency_key(conn, idempotency_key)
        if found:
            job = get_job(conn, found)
            if job is not None:
                try:
                    log_event("job.create_idempotent_return", job_id=job["job_id"], idempotency_key=idempotency_key)
                except Exception as exc:
                    import logging

                    logging.exception("log_event failed: %s", exc)
                return JSONResponse(status_code=200, content=job)
    job_id = storage_create_job(conn, item.job_type, item.payload, item.max_attempts, idempotency_key)
    try:
        log_event("job.create", job_id=job_id, job_type=item.job_type)
    except Exception as exc:
        import logging

        logging.exception("log_event failed: %s", exc)
    job = get_job(conn, job_id)
    if job is None:
        raise HTTPException(status_code=500, detail="job created but not found")
    return job


@app.get("/jobs/{job_id}")
def get_job_handler(job_id: str):
    """HTTP GET /jobs/{job_id}: return job details or 404 if missing."""
    conn = get_conn()
    job = get_job(conn, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    """HTTP POST /jobs/{job_id}/cancel: request cancellation of a job.

    This performs a best-effort update marking the job as
    `CANCEL_REQUESTED`.
    """
    conn = get_conn()
    job = get_job(conn, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    from ..storage.core import update_job as storage_update_job

    storage_update_job(conn, job_id, status="CANCEL_REQUESTED")
    updated = get_job(conn, job_id)
    if updated is None:
        raise HTTPException(status_code=500, detail="job updated but not found")
    return updated
