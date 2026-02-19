import sqlite3
import tempfile

from fastapi.testclient import TestClient

from jobmanager import api
from jobmanager.storage.core import create_job, get_job, init_db, update_job


def test_api_cancel_then_worker_honors_cancel(tmp_path, monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    try:
        # prepare DB and job
        conn = sqlite3.connect(path, check_same_thread=False)
        init_db(conn)
        jid = create_job(conn, "t", {"a": 1}, max_attempts=2)
        conn.close()

        # point the API package to the DB and call cancel endpoint
        api.DB_PATH = path
        client = TestClient(api.app)
        resp = client.post(f"/jobs/{jid}/cancel")
        assert resp.status_code == 200

        # verify DB shows CANCEL_REQUESTED
        conn2 = sqlite3.connect(path, check_same_thread=False)
        job = get_job(conn2, jid)
        assert job["status"] == "CANCEL_REQUESTED"
        conn2.close()

        # simulate worker reservation, then ensure it observes cancel and marks CANCELED
        from jobmanager.worker import runner as runner_mod

        # ensure the runner opens the same DB used by the API
        runner_mod.DB_PATH = path

        # fake reserve_next to mark job RUNNING and return it
        def fake_reserve(conn, worker_id, lease_seconds=10):
            cur = conn.cursor()
            # perform reservation
            cur.execute(
                "UPDATE jobs SET status='RUNNING', worker_id=?, attempt=attempt+1 WHERE job_id=?",
                (worker_id, jid),
            )
            conn.commit()
            # simulate an external cancel arriving immediately after reservation
            cur.execute("UPDATE jobs SET status='CANCEL_REQUESTED' WHERE job_id=?", (jid,))
            conn.commit()
            from jobmanager.storage.core import get_job as real_get

            return real_get(conn, jid)

        monkeypatch.setattr("jobmanager.worker.runner.reserve_next", fake_reserve)

        # run the worker iteration; it will call storage.get_job and see CANCEL_REQUESTED
        processed = runner_mod.run_once("w-cancel-e2e")
        assert processed == jid

        # finally, verify job marked CANCELED
        conn3 = sqlite3.connect(path, check_same_thread=False)
        final = get_job(conn3, jid)
        assert final["status"] == "CANCELED"
        conn3.close()
    finally:
        try:
            import os

            os.unlink(path)
        except Exception:
            pass


def test_worker_finalizes_pre_canceled_job_without_consuming_attempts(tmp_path):
    fd, path = tempfile.mkstemp(suffix=".db")
    try:
        conn = sqlite3.connect(path, check_same_thread=False)
        init_db(conn)
        jid = create_job(conn, "t", {"a": 1}, max_attempts=2)
        update_job(conn, jid, status="CANCEL_REQUESTED")
        conn.close()

        from jobmanager.worker import runner as runner_mod

        runner_mod.DB_PATH = path
        processed = runner_mod.run_once("w-pre-cancel")
        assert processed == jid

        conn2 = sqlite3.connect(path, check_same_thread=False)
        final = get_job(conn2, jid)
        assert final["status"] == "CANCELED"
        assert final["attempt"] == 0
        conn2.close()
    finally:
        try:
            import os

            os.unlink(path)
        except Exception:
            pass
