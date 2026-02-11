# OP_RUNBOOK — Operations and troubleshooting

This runbook provides quick operational procedures for common incidents: migrations, stuck jobs, worker restarts, queue growth, and evidence collection.

References:

- Local execution: [docs/RUN.md](RUN.md)
- Cancellation semantics: [docs/adr/0003-cancel-semantics.md](adr/0003-cancel-semantics.md)
- Retry/backoff: [docs/adr/0002-retry-policy.md](adr/0002-retry-policy.md)
- Metrics: `GET /metrics`

## 1) Health checks

- Liveness: `GET /health` → 200 when the process is alive
- Readiness: `GET /ready` → 200 when the service can talk to the DB
- Metrics: `GET /metrics` → JSON with basic counters

## 2) Migrations (Alembic)

Windows / PowerShell:

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -m alembic upgrade head
```

Rollback (use care):

```powershell
python -m alembic downgrade -1
```

## 3) Worker — start/stop

Run in a loop (development):

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -c "from jobmanager.worker.runner import run; run(worker_id='worker-1', poll_interval=1.0)"
```

Run a single iteration (useful for debugging):

```powershell
python -c "from jobmanager.worker.runner import run_once; print(run_once(worker_id='worker-1'))"
```

## 4) Stuck/orphaned jobs (expired lease)

Symptoms:

- Jobs in `RUNNING` longer than the lease
- High `orphaned_running` in `/metrics`

Inspect via SQLite (example):

```sql
SELECT job_id, status, locked_until, worker_id, attempt, max_attempts
FROM jobs
WHERE status='RUNNING'
ORDER BY locked_until ASC;
```

Manual requeue (use care):

```sql
UPDATE jobs
SET status='QUEUED', locked_until=NULL, worker_id=NULL, updated_at=datetime('now')
WHERE job_id='...';
```

Note: the system is designed so that when `locked_until` expires, the job becomes eligible for reservation again.

## 5) Investigating retries

Retries happen when the worker marks `FAILED_RETRYABLE` and sets `next_run_at`.

Checklist:

- `attempt` e `max_attempts`
- `last_error`
- `next_run_at`

Query:

```sql
SELECT job_id, status, attempt, max_attempts, next_run_at, last_error
FROM jobs
WHERE status IN ('FAILED_RETRYABLE','FAILED_FINAL')
ORDER BY updated_at DESC;
```

## 6) Cancellation (best-effort)

Semantics:

- API marks `CANCEL_REQUESTED`.
- Worker cooperates: after reservation, it re-reads and, if `CANCEL_REQUESTED`, marks `CANCELED`.

Query:

```sql
SELECT job_id, status, locked_until, worker_id
FROM jobs
WHERE status IN ('CANCEL_REQUESTED','CANCELED')
ORDER BY updated_at DESC;
```

## 7) Evidence collection (artifacts)

Save under the artifacts directory:

- [docs/artifacts/README.md](artifacts/README.md)

Suggested checklist:

- JSON logs for the period (stdout)
- `/metrics` dump
- SQL queries used
- GitHub Actions run link/screenshot

## 8) Contacts

- Contact: Jeferson Oliveira de Sousa — jefersonoliveiradesousa681@gmail.com
