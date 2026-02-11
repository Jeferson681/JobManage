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

Demo (gera jobs e demonstra fluxo):

```powershell
.venv\Scripts\Activate.ps1
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python scripts\demo.py
```

Testes:

```powershell
python -m pytest -q
```

## Documentação (principal em docs/)

- Hub técnico: [docs/README-TECH.md](docs/README-TECH.md)
- Como rodar/reproduzir cenários: [docs/RUN.md](docs/RUN.md)
- Contrato da API: [docs/API_CONTRACT.md](docs/API_CONTRACT.md)
- Operação/Incidentes: [docs/OP_RUNBOOK.md](docs/OP_RUNBOOK.md)
- Decisões e ADRs: [docs/DECISIONS.md](docs/DECISIONS.md)
- Diagramas: [docs/diagrams/README.md](docs/diagrams/README.md)

## Evidências (assist_run)

Links diretos (para abrir no GitHub):

- Demo output (texto): [docs/artifacts/assist_run/demo_output.txt](docs/artifacts/assist_run/demo_output.txt)
- Demo output (imagem): [docs/artifacts/assist_run/demo_output.png](docs/artifacts/assist_run/demo_output.png)
- DB dump (JSON): [docs/artifacts/assist_run/jobs_db_dump.json](docs/artifacts/assist_run/jobs_db_dump.json)
- Metrics (texto): [docs/artifacts/assist_run/metrics.txt](docs/artifacts/assist_run/metrics.txt)
- Metrics (imagem): [docs/artifacts/assist_run/metrics.png](docs/artifacts/assist_run/metrics.png)
- Health (texto): [docs/artifacts/assist_run/health.txt](docs/artifacts/assist_run/health.txt)
- Health (imagem): [docs/artifacts/assist_run/health.png](docs/artifacts/assist_run/health.png)
- Coverage (XML): [docs/artifacts/assist_run/coverage.xml](docs/artifacts/assist_run/coverage.xml)
- Coverage (HTML): [docs/artifacts/assist_run/coverage_html](docs/artifacts/assist_run/coverage_html)

Prévia rápida:

![Demo output](docs/artifacts/assist_run/demo_output.png)

![Metrics](docs/artifacts/assist_run/metrics.png)

## Licença

MIT — ver [LICENSE](LICENSE).
