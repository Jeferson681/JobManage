# Operational Runbook

This runbook contains quick recovery and operational steps for the JobManager scaffold.

1. Start locally
- Create a venv and install dev deps: `python -m venv .venv && .venv\Scripts\pip install -r requirements-dev.txt`
- Run the API for local testing: `uvicorn jobmanager.api.app:app --reload`

2. Health checks
- Liveness: GET `/health` — returns 200 when process is running.
- Readiness: GET `/ready` — returns 200 when DB is reachable.
- Metrics: GET `/metrics` — returns basic JSON operational counts.

3. Typical recovery steps
- If the API cannot access the DB, ensure `JOBMANAGER_DB` points to a writable file and that file exists.
- To reinitialize schema: run a small script that calls `jobmanager.storage.core.init_db(conn)` against the DB.

4. Worker troubleshooting
- The worker uses optimistic reservation. If jobs are stuck in `RUNNING` with expired `locked_until`, they will be counted as orphaned in `/metrics`.
- To requeue a stuck job manually: `UPDATE jobs SET status='QUEUED', locked_until=NULL, worker_id=NULL WHERE job_id = '<id>'`.

5. Logs
- Logs are emitted as JSON on the `jobmanager` logger. Look for `event` fields like `job.created`, `job.reserved`, `job.succeeded`, `job.failed`.

6. Alerts and monitoring
- Add alerting for high `FAILED_RETRYABLE` counts or rapidly growing `QUEUED` counts.

7. Contacts and runbook owner
- Owner: Project maintainer
