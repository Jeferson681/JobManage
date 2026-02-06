import os
import sqlite3
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from . import storage
from .schemas import JobCreate

app = FastAPI(title="JobManager (dev scaffold)")

DB_PATH = os.getenv("JOBMANAGER_DB", ":memory:")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@app.on_event("startup")
def startup():
    conn = get_conn()
    storage.init_db(conn)


@app.post("/jobs")
def create_job(item: JobCreate, idempotency_key: Optional[str] = Header(None)):
    conn = get_conn()
    if idempotency_key:
        found = storage.find_by_idempotency_key(conn, idempotency_key)
        if found:
            job = storage.get_job(conn, found)
            return JSONResponse(status_code=200, content={"job_id": job["job_id"], "status": job["status"]})
    job_id = storage.create_job(conn, item.job_type, item.payload, item.max_attempts, idempotency_key)
    return {"job_id": job_id, "status": "QUEUED"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    conn = get_conn()
    job = storage.get_job(conn, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    conn = get_conn()
    job = storage.get_job(conn, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    storage.update_job(conn, job_id, status="CANCEL_REQUESTED")
    return {"job_id": job_id, "status": "CANCEL_REQUESTED"}
