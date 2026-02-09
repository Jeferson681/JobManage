import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,
  payload TEXT NOT NULL,
  idempotency_key TEXT,
  status TEXT NOT NULL,
  attempt INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  next_run_at TEXT,
  locked_until TEXT,
  worker_id TEXT,
  result TEXT,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_idempotency ON jobs (idempotency_key);
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize the jobs schema on the given SQLite connection.

    This operation is idempotent and safe to call multiple times.
    """
    cur = conn.cursor()
    cur.executescript(DB_SCHEMA)
    conn.commit()


def _now_iso() -> str:
    """Return the current UTC time as an ISO formatted string."""
    return datetime.now(timezone.utc).isoformat()


def create_job(
    conn: sqlite3.Connection,
    job_type: str,
    payload: dict,
    max_attempts: int = 3,
    idempotency_key: Optional[str] = None,
) -> str:
    """Create a new job and persist it to the database.

    The `payload` is stored as JSON. Returns the generated `job_id`.
    """
    job_id = str(uuid.uuid4())
    now = _now_iso()
    cur = conn.cursor()
    sql_insert = (
        "INSERT INTO jobs (job_id, job_type, payload, idempotency_key, status, attempt, "
        "max_attempts, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)"
    )
    cur.execute(
        sql_insert,
        (job_id, job_type, json.dumps(payload), idempotency_key, "QUEUED", max_attempts, now, now),
    )
    conn.commit()
    return job_id


def find_by_idempotency_key(conn: sqlite3.Connection, key: str) -> Optional[str]:
    """Return the `job_id` for a given idempotency key, or `None` if missing."""
    cur = conn.cursor()
    cur.execute("SELECT job_id FROM jobs WHERE idempotency_key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else None


def get_job(conn: sqlite3.Connection, job_id: str) -> Optional[dict]:
    """Fetch a job by `job_id` and decode JSON fields.

    Returns a dict or `None` if not found.
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = cur.fetchone()
    if not row:
        return None
    cols = [c[0] for c in cur.description]
    data = dict(zip(cols, row))
    data["payload"] = json.loads(data["payload"]) if data.get("payload") else None
    data["result"] = json.loads(data["result"]) if data.get("result") else None
    data["last_error"] = json.loads(data["last_error"]) if data.get("last_error") else None
    return data


def reserve_next(conn: sqlite3.Connection, worker_id: str, lease_seconds: int = 30) -> Optional[dict]:
    """Reserve the next available queued job for the provided worker.

    The function selects a candidate and attempts to atomically claim it by
    updating `locked_until` and `status`. Returns the claimed job dict or
    `None` when no candidate is available.
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    lease_until = (now + timedelta(seconds=lease_seconds)).isoformat()
    cur = conn.cursor()
    # Atomic-ish reservation: find candidate, then update if still unlocked
    sql_select = (
        "SELECT job_id FROM jobs WHERE status = 'QUEUED' "
        "AND (next_run_at IS NULL OR next_run_at <= ?) "
        "AND (locked_until IS NULL OR locked_until <= ?) "
        "ORDER BY next_run_at ASC LIMIT 1"
    )
    cur.execute(sql_select, (now_iso, now_iso))
    row = cur.fetchone()
    if not row:
        return None
    job_id = row[0]
    sql_update = (
        "UPDATE jobs SET status = 'RUNNING', worker_id = ?, locked_until = ?, "
        "attempt = attempt + 1, updated_at = ? "
        "WHERE job_id = ? AND (locked_until IS NULL OR locked_until <= ?)"
    )
    cur.execute(sql_update, (worker_id, lease_until, _now_iso(), job_id, now_iso))
    if cur.rowcount == 0:
        conn.commit()
        return None
    conn.commit()
    return get_job(conn, job_id)


def update_job(conn: sqlite3.Connection, job_id: str, **fields) -> None:
    """Update a job's allowed fields in a safe, parameterized way.

    Only a pre-approved set of columns may be updated via this helper. This
    prevents accidental SQL-injection vectors if callers pass unexpected
    field names.
    """
    if not fields:
        return

    # Use a mapping of allowed fields to fixed parameterized SQL statements.
    QUERIES = {
        "status": "UPDATE jobs SET status = ?, updated_at = ? WHERE job_id = ?",
        "result": "UPDATE jobs SET result = ?, updated_at = ? WHERE job_id = ?",
        "last_error": "UPDATE jobs SET last_error = ?, updated_at = ? WHERE job_id = ?",
        "locked_until": "UPDATE jobs SET locked_until = ?, updated_at = ? WHERE job_id = ?",
        "worker_id": "UPDATE jobs SET worker_id = ?, updated_at = ? WHERE job_id = ?",
        "next_run_at": "UPDATE jobs SET next_run_at = ?, updated_at = ? WHERE job_id = ?",
        "attempt": "UPDATE jobs SET attempt = ?, updated_at = ? WHERE job_id = ?",
        "max_attempts": "UPDATE jobs SET max_attempts = ?, updated_at = ? WHERE job_id = ?",
        "idempotency_key": "UPDATE jobs SET idempotency_key = ?, updated_at = ? WHERE job_id = ?",
        "payload": "UPDATE jobs SET payload = ?, updated_at = ? WHERE job_id = ?",
    }

    cur = conn.cursor()
    for k, v in fields.items():
        if k not in QUERIES:
            raise ValueError(f"field '{k}' is not allowed to be updated")

        if isinstance(v, (dict, list)):
            val = json.dumps(v)
        else:
            val = v

        cur.execute(QUERIES[k], (val, _now_iso(), job_id))

    conn.commit()
