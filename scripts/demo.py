"""Small demo script to create and process a job locally using the package API.

Usage:
    python scripts/demo.py
"""

import sqlite3

from jobmanager import api as api_mod
from jobmanager.schemas import JobCreate
from jobmanager.storage.core import init_db
from jobmanager.worker import runner as runner_mod


def main():
    """Create a demo job and run one worker iteration.

    This simple docstring satisfies linters which require public functions
    to have a docstring.
    """
    db = "demo.sqlite"
    api_mod.DB_PATH = db
    runner_mod.DB_PATH = db

    conn = sqlite3.connect(db, check_same_thread=False)
    init_db(conn)
    conn.close()

    # create a job
    resp = api_mod.create_job(JobCreate(job_type="demo", payload={"hello": "world"}), idempotency_key=None)
    print("Created job:", resp)

    # run a worker iteration
    processed = runner_mod.run_once("demo-worker")
    print("Worker processed:", processed)


if __name__ == "__main__":
    main()
