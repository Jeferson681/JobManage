# README-TECH — JobManager (hub técnico)

JobManager é um sistema de orquestração de jobs baseado em **lease**, com foco em coordenação via banco de dados: concorrência controlada, estados explícitos, política de retry robusta e sinais operacionais mínimos.

Este é o **hub técnico** do JobManager (ponto de entrada para leitura técnica e revisão rápida).

## Princípios do sistema

- Banco como coordenador (sem fila externa)
- Execução orientada por estado (máquina de estados explícita)
- Reserva por lease para exclusividade temporária
- Retry com jitter para estabilidade sob falhas
- Idempotência na criação de jobs
- Observabilidade nativa (health/ready/metrics + logs)

## Navegação rápida

- Como rodar e reproduzir cenários: [docs/RUN.md](RUN.md)
- Contrato da API: [docs/API_CONTRACT.md](API_CONTRACT.md)
- Operação (runbook): [docs/OP_RUNBOOK.md](OP_RUNBOOK.md)
- Decisões e ADRs: [docs/DECISIONS.md](DECISIONS.md) e [docs/adr/](adr/)
- Diagramas: [docs/diagrams/](diagrams/)
- Evidências (galeria): [docs/artifacts/GALLERY.md](artifacts/GALLERY.md)

## Arquitetura (resumo)

Componentes:

- **API (FastAPI)**: cria jobs, consulta status, solicita cancelamento, expõe health/ready/metrics.
- **Worker**: faz polling no banco, reserva por lease e executa jobs.
- **Banco (SQLite por padrão)**: é a fonte da verdade (jobs + estados + locks + agendamento de retry).

Decisão consciente: o banco também funciona como **mecanismo de coordenação** (sem uso de fila externa), evidenciando controle de concorrência via lease e execução dirigida por estado.

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

O campo `status` representa comportamento: transições são controladas e validadas, reduzindo estados inválidos/ambíguos e tornando o fluxo do job auditável.

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

O worker implementa execução cooperativa e resiliente: reserva por lease e revalida estado antes de executar, para proteger consistência sob concorrência.

Comportamentos documentáveis:

- Reserva: `reserve_next(conn, worker_id, lease_seconds=...)` (status `QUEUED` ou `FAILED_RETRYABLE`, respeita `next_run_at` e `locked_until`).
- Execução: o scaffold atual simula execução (marca `SUCCEEDED`).
- Cancelamento cooperativo: após reservar, reconsulta o job e, se `CANCEL_REQUESTED`, marca `CANCELED`.

### Retry / backoff

Em caso de exceção durante a execução, aplica:

- Exponencial com full jitter: `delay = uniform(0, min(300, base ** attempt))`
- Marca `FAILED_RETRYABLE` e seta `next_run_at`.
- Quando `attempt >= max_attempts`, marca `FAILED_FINAL`.

A intenção é evitar *thundering herd* e manter o sistema estável e previsível sob falhas intermitentes.

ADR: [docs/adr/0002-retry-policy.md](adr/0002-retry-policy.md).

## Observabilidade

Observabilidade é tratada como requisito de primeira classe, permitindo inspecionar externamente o ciclo de vida dos jobs.

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

Os testes validam semântica de comportamento e invariantes do sistema, não apenas detalhes internos de implementação.

CI: workflow em [ .github/workflows/tests.yml](../.github/workflows/tests.yml) (coverage mínimo 90%).

## Artefatos e evidências

Os artefatos e evidências do projeto ficam em `docs/artifacts/`.

- Galeria (capturas organizadas): [docs/artifacts/GALLERY.md](artifacts/GALLERY.md)
- Execução assistida (arquivos): `docs/artifacts/assist_run/`

Exemplos de evidências:

- Saída do `scripts/demo.py`
- Coverage XML
- Logs JSON de um cenário de retry/cancel
- Capturas do GitHub Actions passando

### Tamanho de arquivos (para GitHub)

- Prefira arquivos pequenos e texto (TXT/MD/JSON) sempre que possível.
- PNGs pequenos (screenshots de texto, métricas, gráficos gerados) são aceitáveis para visualização no GitHub.
- Não versionar bases de dados grandes ou arquivos com dados sensíveis; prefira dumps filtrados e texto.

Diagramas vivem em `docs/diagrams/` e devem ser mantidos legíveis e pequenos.
