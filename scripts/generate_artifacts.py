import json
import sqlite3
from datetime import datetime, timezone


def generate(db_path: str, out_dir: str = "docs/artifacts/assist_run") -> None:
    """Generate `metrics.txt` and `health.txt` from the sqlite DB at `db_path`.

    Args:
        db_path: path to the sqlite database file containing the `jobs` table.
        out_dir: directory where `metrics.txt` and `health.txt` will be written.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
    jobs_by_status = {row[0]: int(row[1]) for row in cur.fetchall()}
    cur.execute("SELECT COUNT(*) FROM jobs WHERE status = 'FAILED_RETRYABLE'")
    retry_jobs = int(cur.fetchone()[0])
    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "SELECT COUNT(*) FROM jobs WHERE status = 'RUNNING' AND locked_until IS NOT NULL AND locked_until <= ?",
        (now_iso,),
    )
    orphaned_running = int(cur.fetchone()[0])

    metrics = {
        "jobs_by_status": jobs_by_status,
        "retry_jobs": retry_jobs,
        "orphaned_running": orphaned_running,
    }

    with open(f"{out_dir}/metrics.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps(metrics))

    with open(f"{out_dir}/health.txt", "w", encoding="utf-8") as f:
        f.write(json.dumps({"status": "ok"}))


if __name__ == "__main__":
    import argparse
    import os

    p = argparse.ArgumentParser()
    p.add_argument("--db", default="docs/artifacts/assist_run/demo.db")
    p.add_argument("--out", default="docs/artifacts/assist_run")
    args = p.parse_args()
    os.makedirs(args.out, exist_ok=True)
    generate(args.db, args.out)
