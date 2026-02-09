import os
import sqlite3
import tempfile

from jobmanager import worker as worker_mod
from jobmanager.storage.core import create_job, init_db
from jobmanager.worker.runner import run_once

fd, path = tempfile.mkstemp(suffix=".db")
os.close(fd)
print("db path:", path)
conn = sqlite3.connect(path, check_same_thread=False)
init_db(conn)
jid = create_job(conn, "test", {"x": 1}, max_attempts=1)
print("created job_id:", jid)
conn.close()

worker_mod.DB_PATH = path
worker_mod.DB_PATH = path

# show rows before running
conn2 = sqlite3.connect(path, check_same_thread=False)
print("rows before:", list(conn2.execute("SELECT job_id,status,attempt,next_run_at,locked_until,worker_id FROM jobs")))
conn2.close()

print("calling run_once...")
processed = run_once(worker_id="test-worker")
print("run_once returned:", processed)

conn3 = sqlite3.connect(path, check_same_thread=False)
print("rows after:", list(conn3.execute("SELECT job_id,status,attempt,next_run_at,locked_until,worker_id FROM jobs")))
conn3.close()
