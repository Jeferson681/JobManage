import os
import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from jobmanager.api.app import app
from jobmanager.storage.core import create_job, get_job, init_db, update_job


def test_health_ok():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ready_ok_with_temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        from jobmanager import api as api_mod

        api_mod.DB_PATH = path
        client = TestClient(app)

        resp = client.get("/ready")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def test_metrics_empty_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        from jobmanager import api as api_mod

        api_mod.DB_PATH = path

        # ensure schema exists
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        conn.close()

        client = TestClient(app)
        resp = client.get("/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert body["jobs_by_status"] == {}
        assert body["retry_jobs"] == 0
        assert body["orphaned_running"] == 0
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def test_metrics_counts_jobs_and_orphans():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        init_db(conn)

        # QUEUED
        queued_id = create_job(conn, "t", {"a": 1})

        # FAILED_RETRYABLE
        retry_id = create_job(conn, "t", {"b": 2})
        update_job(conn, retry_id, status="FAILED_RETRYABLE")

        # RUNNING with expired lock (orphaned)
        orphan_id = create_job(conn, "t", {"c": 3})
        expired = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
        update_job(conn, orphan_id, status="RUNNING", locked_until=expired, worker_id="w")

        # sanity: rows exist
        assert get_job(conn, queued_id) is not None
        assert get_job(conn, retry_id) is not None
        assert get_job(conn, orphan_id) is not None
        conn.close()

        from jobmanager import api as api_mod

        api_mod.DB_PATH = path
        client = TestClient(app)
        resp = client.get("/metrics")
        assert resp.status_code == 200
        body = resp.json()

        assert body["jobs_by_status"]["QUEUED"] == 1
        assert body["jobs_by_status"]["FAILED_RETRYABLE"] == 1
        assert body["jobs_by_status"]["RUNNING"] == 1
        assert body["retry_jobs"] == 1
        assert body["orphaned_running"] == 1
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass
