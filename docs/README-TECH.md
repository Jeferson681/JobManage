# README-TECH — JobManager (hub técnico)

Este é o **ponto central** da documentação técnica do JobManager.

Objetivo do projeto: um laboratório backend (API + worker + banco como fila) para aprender semântica de jobs, concorrência, retry/backoff, cancelamento best-effort e observabilidade mínima.

## Navegação rápida

- Como rodar e reproduzir cenários: [docs/RUN.md](RUN.md)
- Contrato da API (o que a API promete hoje): [docs/API_CONTRACT.md](API_CONTRACT.md)
- Operação/Incidentes (runbook): [docs/OP_RUNBOOK.md](OP_RUNBOOK.md)
- Decisões (índice) e ADRs: [docs/DECISIONS.md](DECISIONS.md) e [docs/adr/](adr/)
- Diagramas (Mermaid): [docs/diagrams/](diagrams/)
- Handover (template): [docs/HANDOVER.md](HANDOVER.md)
- Artefatos/Evidências (placeholders): [docs/artifacts/README.md](artifacts/README.md)

## Arquitetura (resumo)

Componentes:

- **API (FastAPI)**: cria jobs, consulta status, solicita cancelamento, expõe health/ready/metrics.
- **Worker**: faz polling no banco, reserva por lease e executa jobs.
- **Banco (SQLite por padrão)**: é a fonte da verdade (jobs + estados + locks + agendamento de retry).

Diagrama conceitual: veja [docs/diagrams/architecture.md](diagrams/architecture.md).

## Modelo de dados (jobs)

Fonte da verdade: tabela `jobs` (SQLite).

Campos principais (intenção):

- `job_id`: identidade e rastreio.
- `status`: máquina de estados explícita (ver [state machine](diagrams/02_state_machine.md)).
- `attempt` / `max_attempts`: controle de retry.
- `locked_until` / `worker_id`: lease para exclusividade temporária.
- `next_run_at`: agendamento (retry/backoff) — o worker só reserva quando estiver “due”.
- `payload`, `result`, `last_error`: auditabilidade (JSON serializado no banco).

Referências:

- Schema em runtime: [src/jobmanager/storage/core.py](../src/jobmanager/storage/core.py)
- Migração Alembic inicial: [alembic/versions/0001_create_jobs.py](../alembic/versions/0001_create_jobs.py)

## API (o que existe hoje)

Implementação: [src/jobmanager/api/app.py](../src/jobmanager/api/app.py)

Endpoints:

- `POST /jobs`
  - Request: `{ job_type, payload, max_attempts? }`
  - Idempotência: via header `Idempotency-Key` (opcional)
  - Response (hoje): Job completo (mesmo formato do `GET /jobs/{job_id}`)
- `GET /jobs/{job_id}`
  - Response: job completo (inclui `payload/result/last_error` decodificados)
- `POST /jobs/{job_id}/cancel`
  - Semântica: best-effort; marca `CANCEL_REQUESTED`
  - Response (hoje): Job completo (com `status = CANCEL_REQUESTED`)

Detalhes completos: [docs/API_CONTRACT.md](API_CONTRACT.md).

## Worker (internals)

Implementação: [src/jobmanager/worker/runner.py](../src/jobmanager/worker/runner.py)

Comportamentos documentáveis:

- Reserva: `reserve_next(conn, worker_id, lease_seconds=...)` (status `QUEUED` ou `FAILED_RETRYABLE`, respeita `next_run_at` e `locked_until`).
- Execução: o scaffold atual simula sucesso imediato (marca `SUCCEEDED`).
- Cancelamento cooperativo: após reservar, reconsulta o job e, se `CANCEL_REQUESTED`, marca `CANCELED`.

### Retry / backoff

Em caso de exceção durante a execução, aplica:

- Exponencial com full jitter: `delay = uniform(0, min(300, base ** attempt))`
- Marca `FAILED_RETRYABLE` e seta `next_run_at`.
- Quando `attempt >= max_attempts`, marca `FAILED_FINAL`.

ADR: [docs/adr/0002-retry-policy.md](adr/0002-retry-policy.md).

## Observabilidade

Logs:

- JSON via `log_event(event, **fields)` em [src/jobmanager/logging.py](../src/jobmanager/logging.py)
- Eventos esperados: `job.created`, `job.reserved`, `job.succeeded`, `job.failed`, `job.failed_final`, `job.canceled`, `job.status_changed`

Endpoints:

- `GET /health`: liveness
- `GET /ready`: readiness (consegue falar com o DB)
- `GET /metrics`: contagens básicas (`jobs_by_status`, `retry_jobs`, `orphaned_running`)

Runbook: [docs/OP_RUNBOOK.md](OP_RUNBOOK.md).

## Migrações (Alembic)

O projeto inclui scaffold do Alembic. Para instruções reprodutíveis (Windows/Linux), ver [docs/RUN.md](RUN.md).

## Testes e estratégia

Estrutura:

- Unit: `tests/unit/`
- Integration: `tests/integration/`
- E2E: `tests/e2e/`

O foco dos testes é provar semântica: idempotência, lease/concorrência, retry+jitter determinístico e cancelamento cooperativo.

CI: workflow em [ .github/workflows/tests.yml](../.github/workflows/tests.yml) (coverage mínimo 90%).

## Artefatos e evidências

Para portfólio, esta pasta é o “envelope” de evidências reprodutíveis:

- [docs/artifacts/README.md](artifacts/README.md)

Execução assistida (artefatos gerados localmente): `docs/artifacts/assist_run/`.

Sugestão de evidências:

- Saída do `scripts/demo.py`
- Coverage XML
- Logs JSON de um cenário de retry/cancel
- Prints do GitHub Actions passando
