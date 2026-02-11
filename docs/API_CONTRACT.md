# API Contract — JobManager

This document defines the JobManager minimum API **as implemented today**.

Base URL: `/` (service root)

Implementation: [src/jobmanager/api/app.py](../src/jobmanager/api/app.py)

## Models

### JobCreate (request)

```json
{
  "job_type": "string",
  "payload": {},
  "max_attempts": 3
}
```

Notes:

- `max_attempts` is optional (default: 3).
- There is no `idempotency_key` field in the request body.

### Job (GET response)

`GET /jobs/{job_id}` returns an object with persisted fields. Example (partial):

```json
{
  "job_id": "uuid",
  "job_type": "string",
  "payload": {},
  "status": "QUEUED|RUNNING|SUCCEEDED|FAILED_RETRYABLE|FAILED_FINAL|CANCEL_REQUESTED|CANCELED",
  "attempt": 0,
  "max_attempts": 3,
  "next_run_at": "2026-02-05T12:00:00Z|null",
  "locked_until": "2026-02-05T12:00:00Z|null",
  "worker_id": "string|null",
  "result": null,
  "last_error": null,
  "started_at": "2026-02-05T12:00:00Z|null",
  "finished_at": "2026-02-05T12:00:00Z|null",
  "created_at": "2026-02-05T12:00:00Z",
  "updated_at": "2026-02-05T12:00:00Z"
}
```

Note: the current implementation uses `datetime.now(timezone.utc).isoformat()`, so timestamps look like `2026-02-05T12:00:00+00:00` (RFC3339/ISO8601 UTC).

## Endpoints

### 1) Create job — `POST /jobs`

- Description: creates a new job.

Idempotency (optional):

  - Header: `Idempotency-Key: <string>`
  - If a job with the same key exists, the API returns the same `job_id` and **does not create a duplicate**.
Request (JSON):

```json
{
  "job_type": "send_email",
  "payload": { "to": "user@example.com", "subject": "Hi" },
  "max_attempts": 5
}
```

Responses (current):

- `200 OK` — created **or** idempotent path.
  - Body: **Job (full object)** (same as `GET /jobs/{job_id}`).
- `400 Bad Request` — validation error

Example (cURL):

```bash
curl -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: abc-123' \
  -d '{"job_type":"send_email","payload":{"to":"x@x","subject":"h"},"max_attempts":3}'
```

### 2) Get job — `GET /jobs/{job_id}`

- Description: returns job state and metadata.
- Responses:
  - `200 OK` — job object
  - `404 Not Found` — unknown `job_id`

Example (cURL):

```bash
curl http://localhost:8000/jobs/00000000-0000-0000-0000-000000000000
```

### 3) Cancel job — `POST /jobs/{job_id}/cancel`

- Description: requests cancellation (best-effort). The API marks `CANCEL_REQUESTED`.

Responses (current):

- `200 OK` — Job (full object) with `status = "CANCEL_REQUESTED"`.
- `404 Not Found`

Example (cURL):

```bash
curl -X POST http://localhost:8000/jobs/00000000-0000-0000-0000-000000000000/cancel
```

## Status semantics

- `QUEUED`: waiting for execution.
- `RUNNING`: reserved by a worker (lease active).
- `SUCCEEDED`: finished successfully (terminal).
- `FAILED_RETRYABLE`: failed but eligible for retry (not terminal).
- `FAILED_FINAL`: failed and not eligible (terminal).
- `CANCEL_REQUESTED`: cancel requested (best-effort).
- `CANCELED`: canceled (terminal).

## Idempotency rules

- Idempotency is based on the `Idempotency-Key` header.
- The API returns `200` for both create and idempotent paths.
- Subsequent requests with the same key return the same `job_id` and **do not create duplicates**.

## Error fields

- `last_error` in the job object should be a structured object when present, e.g. `{ "message": "timeout connecting to X", "code": "network_timeout" }`.

## Timestamps and formats

- All timestamps use RFC3339 / ISO8601 UTC strings.

## Notes for implementers

- Cancel is best-effort; workers should check for `CANCEL_REQUESTED` and exit gracefully when possible.
- `locked_until` + `worker_id` implement the lease; if `locked_until` is in the past the job becomes eligible for reservation again.
- `next_run_at` controls scheduling for retries and delayed jobs.

## Local execution examples

Start API (FastAPI/uvicorn):

```powershell
python -m uvicorn jobmanager.api.app:app --reload
```

Seed a job (cURL example above) and run a worker process that polls and reserves jobs.

## Change log

- 2026-02-10: `POST /jobs` and `POST /jobs/{job_id}/cancel` return the full Job object; added `started_at`/`finished_at`
