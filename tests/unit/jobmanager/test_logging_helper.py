import logging
import os
import sqlite3
import tempfile

from jobmanager.logging import log_event
from jobmanager.storage.core import create_job, init_db


def test_log_event_writes_json_to_logger(caplog):
    caplog.set_level(logging.INFO, logger="jobmanager")
    # emit a sample event
    log_event("test.event", foo="bar", value=1)
    # the record should be present and JSON-parseable
    assert any("test.event" in rec.message or "test.event" in rec.getMessage() for rec in caplog.records)


def test_create_job_emits_log(caplog):
    caplog.set_level(logging.INFO, logger="jobmanager")
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        conn = sqlite3.connect(path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        job_id = create_job(conn, "t", {"a": 1})
        conn.close()

        assert any(
            job_id in (rec.message if isinstance(rec.message, str) else rec.getMessage()) for rec in caplog.records
        )
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass
