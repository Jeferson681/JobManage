# README-TECH — JobManager (tech hub)

JobManager is a **lease-based** job orchestration system that uses the database for coordination: controlled concurrency, explicit states, a robust retry policy, and minimal operational signals.

This document is the project's technical entry point.

## System principles

- Database as coordinator (no external queue)
- State-driven execution (explicit state machine)
- Lease-based reservation for temporary exclusivity
- Jittered retry/backoff for stability under transient failures
- Idempotent job creation
- Built-in operability signals (health/ready/metrics + logs)

## Quick navigation

- Run and reproduce scenarios: [docs/RUN.md](RUN.md)
- API contract: [docs/API_CONTRACT.md](API_CONTRACT.md)
- Operations (runbook): [docs/OP_RUNBOOK.md](OP_RUNBOOK.md)
- Decisions and ADRs: [docs/DECISIONS.md](DECISIONS.md) and [docs/adr/](adr/)
- Diagrams: [docs/diagrams/](diagrams/)
- Evidence gallery: [docs/artifacts/GALLERY.md](artifacts/GALLERY.md)

## Architecture (summary)

Components:

- **API (FastAPI)**: creates jobs, reads status, requests cancellation, exposes health/ready/metrics.
- **Worker**: polls the database, reserves jobs via leases, and executes them.
- **Database (SQLite by default)**: source of truth (jobs + state + locks + retry scheduling).

Intentional design choice: the database is also the **coordination mechanism** (no external queue), highlighting lease-based concurrency control and state-driven execution.

Conceptual diagram: see [docs/diagrams/architecture.md](diagrams/architecture.md).

## Data model (jobs)

Source of truth: `jobs` table (SQLite).

Key fields (intent):

- `job_id`: identity and traceability.
- `status`: explicit state machine (see [state machine](diagrams/02_state_machine.md)).
- `attempt` / `max_attempts`: retry control.
- `locked_until` / `worker_id`: lease for temporary exclusivity.
- `next_run_at`: scheduling (retry/backoff) — workers only reserve jobs that are due.
- `payload`, `result`, `last_error`: auditability (JSON serialized in the database).

`status` is treated as behavior: transitions are controlled and validated to reduce invalid/ambiguous states and keep the lifecycle auditable.

References:

- Runtime schema: [src/jobmanager/storage/core.py](../src/jobmanager/storage/core.py)
- Initial Alembic migration: [alembic/versions/0001_create_jobs.py](../alembic/versions/0001_create_jobs.py)

## API (current surface)

Implementation: [src/jobmanager/api/app.py](../src/jobmanager/api/app.py)

Endpoints:

- `POST /jobs`
  - Request: `{ job_type, payload, max_attempts? }`
  - Idempotency: `Idempotency-Key` header (optional)
  - Response: full Job object (same as `GET /jobs/{job_id}`)
- `GET /jobs/{job_id}`
  - Response: full Job object (includes decoded `payload/result/last_error`)
- `POST /jobs/{job_id}/cancel`
  - Semantics: best-effort; marks `CANCEL_REQUESTED`
  - Response: Job object with `status = CANCEL_REQUESTED`

Details: [docs/API_CONTRACT.md](API_CONTRACT.md).

## Worker (internals)

Implementation: [src/jobmanager/worker/runner.py](../src/jobmanager/worker/runner.py)

The worker is cooperative and resilient: it reserves via lease and re-validates state before executing to preserve consistency under concurrency.

Documentable behaviors:

- Reservation: `reserve_next(conn, worker_id, lease_seconds=...)` (status `QUEUED` or `FAILED_RETRYABLE`, respects `next_run_at` and `locked_until`).
- Execution: current scaffold simulates execution (marks `SUCCEEDED`).
- Cooperative cancellation: after reservation, re-reads the job and, if `CANCEL_REQUESTED`, marks `CANCELED`.

### Retry / backoff

On exceptions during execution:

- Exponential full jitter: `delay = uniform(0, min(300, base ** attempt))`
- Marks `FAILED_RETRYABLE` and sets `next_run_at`.
- When `attempt >= max_attempts`, marks `FAILED_FINAL`.

The intent is to avoid thundering herds and keep behavior stable under intermittent failures.

ADR: [docs/adr/0002-retry-policy.md](adr/0002-retry-policy.md).

## Observability

Observability is treated as a first-class requirement: the job lifecycle is inspectable from the outside.

Logs:

- JSON via `log_event(event, **fields)` in [src/jobmanager/logging.py](../src/jobmanager/logging.py)
- Expected events: `job.created`, `job.reserved`, `job.succeeded`, `job.failed`, `job.failed_final`, `job.canceled`, `job.status_changed`

Endpoints:

- `GET /health`: liveness
- `GET /ready`: readiness (database connectivity)
- `GET /metrics`: basic counters (`jobs_by_status`, `retry_jobs`, `orphaned_running`)

Runbook: [docs/OP_RUNBOOK.md](OP_RUNBOOK.md).

## Migrations (Alembic)

The project includes an Alembic scaffold. For reproducible steps (Windows/Linux), see [docs/RUN.md](RUN.md).

## Tests

Layout:

- Unit: `tests/unit/`
- Integration: `tests/integration/`
- E2E: `tests/e2e/`

Tests validate behavioral semantics and system invariants, not just internal implementation details.

CI: workflow in [ .github/workflows/tests.yml](../.github/workflows/tests.yml) (minimum coverage 90%).

## Artifacts and evidence

Project artifacts live under `docs/artifacts/`.

- Gallery (organized screenshots): [docs/artifacts/GALLERY.md](artifacts/GALLERY.md)
- Assisted run (files): `docs/artifacts/assist_run/`

Examples of evidence:

- `scripts/demo.py` output
- Coverage XML
- JSON logs from a retry/cancel scenario
- GitHub Actions screenshots

### File size (GitHub)

- Prefer small text files (TXT/MD/JSON) when possible.
- Small PNGs (text screenshots, metrics) are acceptable for GitHub viewing.
- Do not commit large databases or sensitive data; prefer filtered dumps and text.

Diagrams live in `docs/diagrams/` and should remain readable and small.
