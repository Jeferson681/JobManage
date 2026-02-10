# Decisões (índice) e ADRs

Este arquivo é um **índice** para as decisões do projeto.

Regra prática:

- Decisões “grandes” (arquitetura/semântica) viram ADR em `docs/adr/`.
- Este arquivo aponta para o ADR e pode registrar decisões menores (tooling, convenções).

## ADRs (aceitos)

- [DB como fila (fonte da verdade)](adr/0001-db-as-queue.md)
- [Retry policy (exponencial + full jitter)](adr/0002-retry-policy.md)
- [Cancelamento cooperativo (best-effort)](adr/0003-cancel-semantics.md)

## Convenções e decisões menores

- Linguagem: documentação principal em `docs/` (README raiz só faz “60 segundos” + links).
- Observabilidade mínima: logs JSON + endpoints `/health`, `/ready`, `/metrics`.
- CI: cobertura mínima 90% no workflow de testes.

## Template (para novos ADRs)

Use o mesmo formato dos arquivos em `docs/adr/`.
