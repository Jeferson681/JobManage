"""Load test using Postgres for concurrency-safe reservations.

Usage example:
  export PGHOST=localhost
  export PGUSER=postgres
  export PGPASSWORD=secret
  export PGDATABASE=jobmanager
  python scripts/load_demo_pg.py --workers 5 --jobs 500 --duration 60

This script implements a small subset of the job reservation/update
logic using `psycopg2` and `SELECT ... FOR UPDATE SKIP LOCKED` so it
scales under concurrent worker load.
"""

from __future__ import annotations

import argparse
import threading
import time
import random
import os
from typing import Optional

import psycopg2
import psycopg2.extras


DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  job_id TEXT PRIMARY KEY,
  job_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  idempotency_key TEXT,
  status TEXT NOT NULL,
  attempt INTEGER NOT NULL DEFAULT 0,
  max_attempts INTEGER NOT NULL DEFAULT 3,
  next_run_at TIMESTAMPTZ,
  locked_until TIMESTAMPTZ,
  worker_id TEXT,
  result JSONB,
  last_error JSONB,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_idempotency ON jobs (idempotency_key);
"""


def get_conn(dsn: Optional[str] = None):
    params = {}
    if dsn:
        params['dsn'] = dsn
    else:
        # allow PGHOST/PGUSER/PGPASSWORD/PGDATABASE/PGPORT environ
        pass
    conn = psycopg2.connect(**params)
    conn.autocommit = False
    return conn


def init_db(conn):
    cur = conn.cursor()
    cur.execute(DB_SCHEMA)
    conn.commit()


def create_jobs(conn, total_jobs: int):
    cur = conn.cursor()
    for i in range(total_jobs):
        cur.execute(
            """
            INSERT INTO jobs (job_id, job_type, payload, status, attempt, max_attempts, created_at, updated_at)
            VALUES (gen_random_uuid()::text, %s, %s::jsonb, 'QUEUED', 0, %s, now(), now())
            """,
            ("load_test", psycopg2.extras.Json({"n": i}), 3),
        )
    conn.commit()


def reserve_next(conn, worker_id: str, lease_seconds: int = 30):
    # Use a transaction with SELECT FOR UPDATE SKIP LOCKED to avoid races
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("BEGIN")
        cur.execute(
            """
            SELECT job_id, status
            FROM jobs
            WHERE (status = 'QUEUED' OR status = 'FAILED_RETRYABLE' OR status = 'CANCEL_REQUESTED')
              AND (next_run_at IS NULL OR next_run_at <= now())
            ORDER BY next_run_at NULLS FIRST
            FOR UPDATE SKIP LOCKED
            LIMIT 1
            """,
        )
        row = cur.fetchone()
        if not row:
            conn.rollback()
            return None

        job_id = row['job_id']
        status = row['status']

        if status == 'CANCEL_REQUESTED':
            cur.execute(
                "UPDATE jobs SET status='CANCELED', finished_at = now(), locked_until = NULL, worker_id = NULL, updated_at = now() WHERE job_id = %s",
                (job_id,)
            )
            conn.commit()
            return get_job(conn, job_id)

        lease_until = f"now() + interval '{lease_seconds} seconds'"
        # update and increment attempt
        cur.execute(
            f"""
            UPDATE jobs
            SET status='RUNNING', worker_id=%s, locked_until = {lease_until},
                attempt = attempt + 1, started_at = COALESCE(started_at, now()), updated_at = now()
            WHERE job_id = %s
            RETURNING *
            """,
            (worker_id, job_id),
        )
        updated = cur.fetchone()
        conn.commit()
        return updated
    except Exception:
        conn.rollback()
        raise


def get_job(conn, job_id: str):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    return cur.fetchone()


def update_job(conn, job_id: str, **fields):
    if not fields:
        return
    allowed = {
        'status', 'result', 'last_error', 'locked_until', 'worker_id', 'next_run_at', 'attempt', 'max_attempts', 'idempotency_key', 'payload', 'started_at', 'finished_at'
    }
    sets = []
    vals = []
    for k, v in fields.items():
        if k not in allowed:
            raise ValueError(f"field '{k}' not allowed")
        sets.append(f"{k} = %s")
        vals.append(v)
    sets.append("updated_at = now()")
    sql = f"UPDATE jobs SET {', '.join(sets)} WHERE job_id = %s"
    vals.append(job_id)
    cur = conn.cursor()
    cur.execute(sql, tuple(vals))
    conn.commit()


def worker_once(conn, worker_id: str):
    job = reserve_next(conn, worker_id, lease_seconds=10)
    if not job:
        return None
    job_id = job['job_id']
    if job.get('status') == 'CANCELED':
        return job_id
    # Re-fetch to honour cancellation
    current = get_job(conn, job_id)
    if current and current.get('status') == 'CANCEL_REQUESTED':
        update_job(conn, job_id, status='CANCELED', finished_at='now()')
        return job_id

    # simulate work and random failure
    if random.random() < 0.3:
        # record retryable failure
        next_run_delay = int(random.uniform(1, 10))
        cur = conn.cursor()
        cur.execute(
            "UPDATE jobs SET status='FAILED_RETRYABLE', last_error = %s, next_run_at = now() + interval %s, worker_id = NULL, locked_until = NULL, updated_at = now() WHERE job_id = %s",
            (psycopg2.extras.Json({'message': 'simulated failure'}), f"'{next_run_delay} seconds'", job_id),
        )
        conn.commit()
        return job_id

    # succeed
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET status='SUCCEEDED', result = %s, finished_at = now(), worker_id = NULL, locked_until = NULL, updated_at = now() WHERE job_id = %s", (psycopg2.extras.Json({'message': 'ok'}), job_id))
    conn.commit()
    return job_id


def worker_loop(dsn: Optional[str], worker_id: str, stop_flag):
    conn = get_conn(dsn)
    try:
        while not stop_flag['stop']:
            try:
                processed = worker_once(conn, worker_id)
            except Exception:
                # small backoff on error
                time.sleep(0.01)
                continue
            if not processed:
                time.sleep(0.05)
    finally:
        conn.close()


def print_stats(conn):
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status")
    rows = cur.fetchall()
    print("\n=== JOB STATS ===")
    for r in rows:
        print(f"{r[0]}: {r[1]}")


def main(dsn: Optional[str], workers: int, jobs: int, duration: int):
    conn = get_conn(dsn)
    conn.autocommit = False
    init_db(conn)

    print("Criando jobs...")
    # Use a separate connection for inserts to reduce lock contention
    inserter = get_conn(dsn)
    create_jobs(inserter, jobs)
    inserter.close()

    stop_flag = {'stop': False}
    threads = []
    print(f"Iniciando {workers} workers...")
    for i in range(workers):
        t = threading.Thread(target=worker_loop, args=(dsn, f"pg-worker-{i}", stop_flag), daemon=True)
        t.start()
        threads.append(t)

    start = time.time()
    try:
        while time.time() - start < duration:
            print_stats(conn)
            time.sleep(2)
    finally:
        stop_flag['stop'] = True
        print('\nFinalizando...')
        for t in threads:
            t.join(timeout=1)
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn', help='Optional psycopg2 DSN')
    parser.add_argument('--workers', type=int, default=5)
    parser.add_argument('--jobs', type=int, default=200)
    parser.add_argument('--duration', type=int, default=30)
    args = parser.parse_args()

    # If no DSN provided, rely on environment variables
    dsn = args.dsn
    main(dsn, args.workers, args.jobs, args.duration)
