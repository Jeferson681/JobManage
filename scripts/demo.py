"""Simple demo script for JobManager.

Shows: create jobs, request cancel, run worker iterations, and demonstrate a retry
by simulating a processing failure for one job.

Usage:
    python scripts/demo.py --db ./demo.db
"""

from __future__ import annotations

import argparse
import sqlite3
import time

from jobmanager.storage import core as storage
from jobmanager.worker import runner


def print_jobs(conn: sqlite3.Connection) -> None:
    """Print a summary of jobs in the DB for demo purposes."""
    cur = conn.cursor()
    cur.execute("SELECT job_id, status, attempt, max_attempts, next_run_at, locked_until, worker_id FROM jobs")
    rows = cur.fetchall()
    print("\nJobs state:")
    for r in rows:
        print(dict(r))


def main(db: str, iterations: int = 10) -> None:
    """Run the demo: create jobs and run worker iterations.

    `db` is a path to a sqlite file used by both storage and worker.
    """
    # point both API/worker modules at the demo DB
    runner.DB_PATH = db

    conn = sqlite3.connect(db, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    storage.init_db(conn)

    # create three jobs
    j1 = storage.create_job(conn, "demo_ok", {"n": 1}, max_attempts=1)
    j2 = storage.create_job(conn, "demo_cancel", {"n": 2}, max_attempts=1)
    j3 = storage.create_job(conn, "demo_retry", {"n": 3}, max_attempts=2)

    print("Created jobs:", j1, j2, j3)

    # request cancel for j2 before worker picks it up
    storage.update_job(conn, j2, status="CANCEL_REQUESTED")

    # simulate a processing failure for j3 by patching runner.update_job so
    # it raises when trying to mark j3 as SUCCEEDED (this triggers retry path)
    real_update = runner.update_job

    def flaky_update(conn_local, job_id, **fields):
        if job_id == j3 and fields.get("status") == "SUCCEEDED":
            raise RuntimeError("simulated processing error for demo")
        return real_update(conn_local, job_id, **fields)

    runner.update_job = flaky_update

    # run worker iterations and show state transitions
    for i in range(iterations):
        print(f"\n=== iteration {i+1} ===")
        processed = runner.run_once(worker_id=f"demo-worker-{i}")
        print("processed:", processed)
        print_jobs(conn)
        # small pause to make output readable
        time.sleep(0.2)

    conn.close()


if __name__ == "__main__":
    import os

    p = argparse.ArgumentParser()
    p.add_argument("--db", default="./demo.db", help="Path to sqlite DB file")
    p.add_argument("--iterations", type=int, default=10)
    args = p.parse_args()
    # ensure directory exists
    db_dir = os.path.dirname(args.db) or "."
    os.makedirs(db_dir, exist_ok=True)
    main(args.db, iterations=args.iterations)
    main(args.db, iterations=args.iterations)
