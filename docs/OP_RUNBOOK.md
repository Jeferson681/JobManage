# Runbook: JobManager (dev scaffold)

Objetivo
--------
Procedimentos operacionais rápidos para incidentes comuns: aplicar migrações, recuperar jobs travados, reiniciar workers e inspecionar métricas.

Atenção inicial
---------------
- Trabalhe em um ambiente com acesso ao banco de dados e às credenciais do deploy.
- Não execute comandos destrutivos em produção sem backup e autorização.

Aplicar migrações
-----------------
1. Defina o banco alvo (ex.: `JOBMANAGER_DB`) apontando para o URL/arquivo.

PowerShell:
```powershell
$Env:JOBMANAGER_DB = 'C:\path\to\jobmanager.db'
C:/Users/Jeferson/OneDrive/Documentos/JobManager/.venv/Scripts/python.exe -m alembic upgrade head
```

Linux/macOS:
```bash
export JOBMANAGER_DB=/path/to/jobmanager.db
.venv/bin/python -m alembic upgrade head
```

Rollback (com cuidado):
```bash
.venv/bin/python -m alembic downgrade -1
```

Iniciar/Parar worker local
--------------------------
- Rodar uma iteração única (útil para testes):
  ```bash
  .venv/bin/python -m jobmanager.worker.runner
  ```
- Rodar em loop (desenvolvimento):
  ```bash
  from jobmanager.worker.runner import run
  run(worker_id='worker-1', poll_interval=1.0)
  ```

Detecção e resolução de jobs travados
------------------------------------
- Sintoma: `RUNNING` por mais tempo que `locked_until` indica ou contagem alta de `RUNNING`/`locked_until` vencidos.
- Inspecionar via SQL:
  ```sql
  SELECT job_id, status, locked_until, worker_id FROM jobs WHERE status='RUNNING';
  SELECT COUNT(*) FROM jobs WHERE status='RUNNING' AND locked_until <= datetime('now');
  ```
- Solução operacional (caso worker tenha caído):
  1. Se o job deve ser reprocessado: marcar `status='QUEUED'`, `locked_until=NULL`, `worker_id=NULL`.
     ```sql
     UPDATE jobs SET status='QUEUED', locked_until=NULL, worker_id=NULL WHERE job_id='...';
     ```
  2. Se for necessário cancelar: `UPDATE jobs SET status='CANCEL_REQUESTED' WHERE job_id='...';` e aguardar worker cooperativo.
  3. Para forçar cancelamento: `UPDATE jobs SET status='CANCELED', locked_until=NULL, worker_id=NULL WHERE job_id='...';` (use com cautela).

Como investigar um job com falhas repetidas
-----------------------------------------
- Verifique `attempt`, `max_attempts`, `last_error`, `next_run_at`.
- Se `FAILED_RETRYABLE` e `next_run_at` distante, é backoff em vigor (jitter aplicado).
- Para reprovar manualmente ou acelerar retry, ajuste `next_run_at` para `datetime('now')`.

Alertas e métricas mínimas
-------------------------
- Alerta sugerido: `FAILED_RETRYABLE` crescendo rapidamente (indicador de downstream instability).
- Alerta sugerido: muitos `QUEUED` sem consumo por > X minutos (worker unhealthy).
- Métricas úteis: counts por `status`, `orphaned_running` (RUNNING com locked_until vencido), tempo médio entre `created_at` e `SUCCEEDED`.

Pré-mortem / pós-incidente curto
--------------------------------
1. Colete logs (JSON) do período incidente com `job_id` relacionado.
2. Capture DB state: `SELECT * FROM jobs WHERE job_id IN (...)`.
3. Se mitigado, documente ação tomada e recursos afetados.
4. Se recorrente, crie um ADR sobre política de retry/backoff ou DLQ.

Contatos & responsabilidades
----------------------------
- Time SRE/ops: responsável por aplicar migrações e restaurar DB.
- Time de Plataforma/Dev: responsável por analisar causas de falhas em `job` e corrigir código.

Notas finais
-----------
- Mantenha este runbook sincronizado com alterações importantes no fluxo de trabalho (retry policy, locking, cancel semantics).
- Para alterações no esquema, gere uma revisão Alembic com mensagem clara e aplique em staging antes de prod.
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
