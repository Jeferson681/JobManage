# API Contract — JobManager

This document defines the minimal API for creating and controlling jobs in the JobManager.

Base URL: `/` (service root)

Schemas

- Job (response)

```json
{
  "job_id": "uuid",
  "job_type": "string",
  "payload": { },
  "idempotency_key": "string|null",
  "status": "QUEUED|RUNNING|SUCCEEDED|FAILED_RETRYABLE|FAILED_FINAL|CANCEL_REQUESTED|CANCELED",
  "attempt": 0,
  "max_attempts": 3,
  "next_run_at": "2026-02-05T12:00:00Z|null",
  "locked_until": "2026-02-05T12:00:00Z|null",
  "worker_id": "string|null",
  "result": null,
  "last_error": null,
  "created_at": "2026-02-05T12:00:00Z",
  "updated_at": "2026-02-05T12:00:00Z"
}
```

Endpoints

1) Create job — `POST /jobs`

- Description: create a new Job. Supports idempotency via `idempotency_key` (in body or `Idempotency-Key` header).
- Request (JSON):

```json
{
  "job_type": "send_email",
  "payload": { "to": "user@example.com", "subject": "Hi" },
  "idempotency_key": "optional-string",
  "max_attempts": 5
}
```

- Responses:
  - `201 Created` — job created. Body: job object (see schema).
  - `200 OK` — idempotent: a job with the same `idempotency_key` already exists; returns existing job (not created again).
  - `400 Bad Request` — validation error.

Example cURL (create):

```bash
curl -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -d '{"job_type":"send_email","payload":{"to":"x@x","subject":"h"},"idempotency_key":"abc-123"}'
```

2) Get job — `GET /jobs/{job_id}`

- Description: retrieve job state and metadata.
- Responses:
  - `200 OK` — job object
  - `404 Not Found` — unknown `job_id`

Example cURL (get):

```bash
curl http://localhost:8000/jobs/00000000-0000-0000-0000-000000000000
```

3) Cancel job — `POST /jobs/{job_id}/cancel`

- Description: request cancellation of a job. Cancellation is best-effort — worker must cooperate. Endpoint records `CANCEL_REQUESTED` and returns current job state.
- Responses:
  - `202 Accepted` — cancel request recorded; body: job object (updated status may be `CANCEL_REQUESTED`).
  - `404 Not Found` — unknown `job_id`.

Example cURL (cancel):

```bash
curl -X POST http://localhost:8000/jobs/00000000-0000-0000-0000-000000000000/cancel
```

Status semantics

- `QUEUED`: waiting for execution.
- `RUNNING`: reserved by a worker (lease active).
- `SUCCEEDED`: finished successfully (terminal).
- `FAILED_RETRYABLE`: failed but eligible for retry (not terminal).
- `FAILED_FINAL`: failed and not eligible (terminal).
- `CANCEL_REQUESTED`: cancel requested (best-effort).
- `CANCELED`: canceled (terminal).

Idempotency rules

- If `idempotency_key` is provided when creating a job, the server must ensure that repeated `POST /jobs` calls with the same `idempotency_key` and equivalent body return the same job instead of creating duplicates.
- Recommended behavior: first request returns `201 Created`; subsequent identical requests return `200 OK` with the existing job object.

Error fields

- `last_error` in the job object should be a structured object when present, e.g. `{ "message": "timeout connecting to X", "code": "network_timeout" }`.

Timestamps and formats

- All timestamps use RFC3339 / ISO8601 UTC strings.

Notes for implementers

- Cancel is best-effort; workers should check for `CANCEL_REQUESTED` and exit gracefully when possible.
- `locked_until` + `worker_id` implement the lease; if `locked_until` is in the past the job becomes eligible for reservation again.
- `next_run_at` controls scheduling for retries and delayed jobs.

Run examples (local dev)

Start API (FastAPI/uvicorn):

```bash
uvicorn jobmanager.api:app --reload
```

Seed a job (curl example above) and run a worker process that polls and reserves jobs.

Change log

- 2026-02-05: initial contract (minimal endpoints + idempotency rules)
