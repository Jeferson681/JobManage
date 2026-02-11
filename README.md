# JobManager — 60 segundos

JobManager é um laboratório backend minimalista para **enfileirar jobs** em banco e **executar via worker**, com semântica explícita (lease, retry, cancel best-effort) e observabilidade mínima.

API:

- `POST /jobs` (idempotência via header `Idempotency-Key`)
- `GET /jobs/{job_id}`
- `POST /jobs/{job_id}/cancel`

## Fluxo (alto nível)

1) A API recebe `POST /jobs` e persiste um job com status `QUEUED`.

2) O worker faz polling no banco e reserva um job elegível via lease (`locked_until` + `worker_id`), marcando `RUNNING`.

3) O worker finaliza marcando `SUCCEEDED` / `FAILED_RETRYABLE` / `FAILED_FINAL` / `CANCELED` e preenchendo timestamps (`started_at`, `finished_at`).

## Rodar rápido (Windows / PowerShell)

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'

# opcional: usar um arquivo SQLite persistente
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"

# API
python -m uvicorn jobmanager.api.app:app --reload --port 8000
```

Worker (em outro terminal):

```powershell
.venv\Scripts\Activate.ps1
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -c "from jobmanager.worker.runner import run; run(worker_id='worker-1', poll_interval=1.0)"
```

````markdown
# JobManager — Overview (60s)

JobManager é um laboratório pequeno: uma API que enfileira jobs e um worker que os executa.

Principais pontos:
- `POST /jobs` — cria job (idempotência via `Idempotency-Key`)
- `GET /jobs/{job_id}` — consulta
- `POST /jobs/{job_id}/cancel` — pedido de cancelamento (best-effort)

Run rápido (PowerShell):

```powershell
.venv\Scripts\Activate.ps1
python -m pip install -e '.[dev]'
python -m uvicorn jobmanager.api.app:app --reload --port 8000
```

Worker (outro terminal):

```powershell
.venv\Scripts\Activate.ps1
python -c "from jobmanager.worker.runner import run; run(worker_id='worker-1', poll_interval=1.0)"
```

Docs técnicas e evidências detalhadas: [docs/README-TECH.md](docs/README-TECH.md)

Licença: MIT — [LICENSE](LICENSE)

````
