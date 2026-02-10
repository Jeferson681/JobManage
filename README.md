# JobManager — 60 segundos

JobManager é um laboratório backend minimalista para **enfileirar jobs** em banco e **executar via worker**, com semântica explícita (lease, retry, cancel best-effort) e observabilidade mínima.

API:

- `POST /jobs` (idempotência via header `Idempotency-Key`)
- `GET /jobs/{job_id}`
- `POST /jobs/{job_id}/cancel`

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
- Evidências (placeholders): [docs/artifacts/README.md](docs/artifacts/README.md)

## Licença

MIT — ver [LICENSE](LICENSE).
