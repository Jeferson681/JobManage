# OP_RUNBOOK — Operação e troubleshooting

Objetivo: procedimentos operacionais rápidos para incidentes comuns: migrações, jobs travados, worker caindo, fila crescendo e coleta de evidências.

Referências:

- Como rodar localmente: [docs/RUN.md](RUN.md)
- Semântica de cancelamento: [docs/adr/0003-cancel-semantics.md](adr/0003-cancel-semantics.md)
- Retry/backoff: [docs/adr/0002-retry-policy.md](adr/0002-retry-policy.md)
- Métricas: `GET /metrics`

## 1) Health checks

- Liveness: `GET /health` → 200 quando o processo está vivo
- Readiness: `GET /ready` → 200 quando o serviço consegue falar com o DB
- Métricas: `GET /metrics` → JSON com contagens básicas

## 2) Migrações (Alembic)

Windows / PowerShell:

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -m alembic upgrade head
```

Rollback (com cuidado):

```powershell
python -m alembic downgrade -1
```

## 3) Worker — como iniciar e parar

Rodar em loop (desenvolvimento):

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -c "from jobmanager.worker.runner import run; run(worker_id='worker-1', poll_interval=1.0)"
```

Rodar uma iteração (útil para depuração):

```powershell
python -c "from jobmanager.worker.runner import run_once; print(run_once(worker_id='worker-1'))"
```

## 4) Jobs travados / órfãos (lease expirado)

Sintoma:

- Jobs em `RUNNING` por tempo maior que o lease
- `orphaned_running` alto em `/metrics`

Inspeção via SQLite (exemplo):

```sql
SELECT job_id, status, locked_until, worker_id, attempt, max_attempts
FROM jobs
WHERE status='RUNNING'
ORDER BY locked_until ASC;
```

Requeue manual (use com cuidado):

```sql
UPDATE jobs
SET status='QUEUED', locked_until=NULL, worker_id=NULL, updated_at=datetime('now')
WHERE job_id='...';
```

Observação: o sistema foi desenhado para que, quando `locked_until` expira, o job volte a ser elegível para reserva automaticamente.

## 5) Investigação de retries

O retry acontece quando o worker marca `FAILED_RETRYABLE` e define `next_run_at`.

Checklist:

- `attempt` e `max_attempts`
- `last_error`
- `next_run_at`

Consulta:

```sql
SELECT job_id, status, attempt, max_attempts, next_run_at, last_error
FROM jobs
WHERE status IN ('FAILED_RETRYABLE','FAILED_FINAL')
ORDER BY updated_at DESC;
```

## 6) Cancelamento (best-effort)

Semântica:

- API marca `CANCEL_REQUESTED`.
- Worker coopera: após reservar, reconsulta e, se `CANCEL_REQUESTED`, marca `CANCELED`.

Consulta:

```sql
SELECT job_id, status, locked_until, worker_id
FROM jobs
WHERE status IN ('CANCEL_REQUESTED','CANCELED')
ORDER BY updated_at DESC;
```

## 7) Coleta de evidências (artefatos)

Salvar no diretório de placeholders:

- [docs/artifacts/README.md](artifacts/README.md)

Checklist sugerido:

- logs JSON do período (stdout)
- dump do `/metrics`
- consultas SQL usadas
- link/print do run do GitHub Actions

## 8) Contatos

- Owner/Maintainer: Jeferson Oliveira de Sousa — jefersonoliveiradesousa681@gmail.com
