# API Contract — JobManager

Este documento define a API mínima do JobManager **conforme implementada hoje**.

Base URL: `/` (service root)

Implementação: [src/jobmanager/api/app.py](../src/jobmanager/api/app.py)

## Modelos

### JobCreate (request)

```json
{
  "job_type": "string",
  "payload": {},
  "max_attempts": 3
}
```

Notas:

- `max_attempts` é opcional (padrão 3).
- Não existe `idempotency_key` no body atualmente.

### Job (response de GET)

`GET /jobs/{job_id}` retorna um objeto com os campos persistidos. Exemplo (parcial):

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
  "created_at": "2026-02-05T12:00:00Z",
  "updated_at": "2026-02-05T12:00:00Z"
}
```

## Endpoints

### 1) Create job — `POST /jobs`

- Description: cria um novo job.

Idempotência (opcional):

- Header: `Idempotency-Key: <string>`
- Se um job com a mesma chave existir, a API retorna o mesmo `job_id` e **não cria duplicado**.
Request (JSON):

```json
{
  "job_type": "send_email",
  "payload": { "to": "user@example.com", "subject": "Hi" },
  "max_attempts": 5
}
```

Responses (hoje):

- `201 Created` — criado. Body: `{ "job_id": "...", "status": "QUEUED" }`
- `200 OK` — idempotente: job já existia. Body: `{ "job_id": "...", "status": "..." }`
- `400 Bad Request` — erro de validação

Example cURL (create):

```bash
curl -X POST http://localhost:8000/jobs \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: abc-123' \
  -d '{"job_type":"send_email","payload":{"to":"x@x","subject":"h"},"max_attempts":3}'
```

### 2) Get job — `GET /jobs/{job_id}`

- Description: retrieve job state and metadata.
- Responses:
  - `200 OK` — job object
  - `404 Not Found` — unknown `job_id`

Example cURL (get):

```bash
curl http://localhost:8000/jobs/00000000-0000-0000-0000-000000000000
```

### 3) Cancel job — `POST /jobs/{job_id}/cancel`

- Description: solicita cancelamento (best-effort). A API marca `CANCEL_REQUESTED`.

Responses (hoje):

- `200 OK` — `{ "job_id": "...", "status": "CANCEL_REQUESTED" }`
- `404 Not Found`

Example cURL (cancel):

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

- A idempotência é baseada no header `Idempotency-Key`.
- Primeira requisição retorna `201`.
- Requisições subsequentes com a mesma chave retornam `200` com o mesmo `job_id`.

## Error fields

- `last_error` in the job object should be a structured object when present, e.g. `{ "message": "timeout connecting to X", "code": "network_timeout" }`.

## Timestamps and formats

- All timestamps use RFC3339 / ISO8601 UTC strings.

## Notes for implementers

- Cancel is best-effort; workers should check for `CANCEL_REQUESTED` and exit gracefully when possible.
- `locked_until` + `worker_id` implement the lease; if `locked_until` is in the past the job becomes eligible for reservation again.
- `next_run_at` controls scheduling for retries and delayed jobs.

## Run examples (local dev)

Start API (FastAPI/uvicorn):

```powershell
python -m uvicorn jobmanager.api.app:app --reload
```

Seed a job (curl example above) and run a worker process that polls and reserves jobs.

## Change log

- 2026-02-10: alinhado com implementação atual (idempotência via header; create/cancel retornam `{job_id, status}`)
