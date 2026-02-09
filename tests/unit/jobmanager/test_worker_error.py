import os
import sqlite3
import tempfile

from jobmanager.storage.core import init_db
from jobmanager.worker import runner as runner_mod


def test_run_once_no_job_returns_none():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        runner_mod.DB_PATH = path
        # empty DB
        conn = sqlite3.connect(path, check_same_thread=False)
        init_db(conn)
        conn.close()

        processed = runner_mod.run_once(worker_id="w-1")
        assert processed is None
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass
