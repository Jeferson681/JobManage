import os
import sqlite3
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from ..schemas import JobCreate
from ..storage.core import create_job as storage_create_job
from ..storage.core import find_by_idempotency_key, get_job, init_db

DB_PATH = os.getenv("JOBMANAGER_DB", ":memory:")


def get_conn():
    """Return a sqlite3 connection using the package-level `DB_PATH`.

    Tests may override `api.DB_PATH` before calling handlers; this function
    reads the package attribute at runtime to respect such overrides.
    """
    # Resolve DB path from package-level attribute if present so tests can override it
    import importlib

    if __package__:
        pkg = importlib.import_module(__package__)
        db_path = getattr(pkg, "DB_PATH", DB_PATH)
    else:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler to ensure the DB schema exists at startup."""
    conn = get_conn()
    init_db(conn)
    yield


app = FastAPI(title="JobManager (dev scaffold)", lifespan=lifespan)


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
                return JSONResponse(status_code=200, content={"job_id": job["job_id"], "status": job["status"]})
    job_id = storage_create_job(conn, item.job_type, item.payload, item.max_attempts, idempotency_key)
    return {"job_id": job_id, "status": "QUEUED"}


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
    return {"job_id": job_id, "status": "CANCEL_REQUESTED"}
