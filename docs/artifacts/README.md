# Artefatos & evidências (placeholders)

Este diretório é reservado para **artefatos reprodutíveis** (evidências) do projeto.

Política:

- Prefira **arquivos pequenos e texto** (JSON/MD/TXT) em vez de binários.
- Se gerar binários (SVG/PNG), considere guardar fora do git e apenas linkar.
- Nunca coloque segredos.

## Estrutura sugerida

- `runs/` — logs e notas de execuções reprodutíveis
  - `runs/YYYY-MM-DD_demo/`
    - `commands.md` (comandos exatos)
    - `stdout.log` (saída)
    - `jobmanager.db` (opcional, se pequeno e sem dados sensíveis)
    - `notes.md` (observações)
- `ci/` — evidências de CI
  - `coverage.xml` (ou link para artifact do Actions)
  - `actions-run.md` (link do run, prints, observações)
- `metrics/` — dumps de `/metrics`
  - `metrics.json`
- `diagrams/` — renders opcionais (SVG) dos Mermaid

## Checklist de evidências (portfólio)

- [ ] Demonstração: `scripts/demo.py` rodando e imprimindo estados finais
- [ ] Cobertura: `coverage report` >= 90% (local e/ou CI)
- [ ] Cenário: idempotência (mesmo `Idempotency-Key` não duplica)
- [ ] Cenário: lease (dois workers não executam o mesmo job)
- [ ] Cenário: retry/backoff com jitter (determinístico em testes)
- [ ] Cenário: cancelamento cooperativo

## Onde isso aparece no código

- Script de demo: [scripts/demo.py](../../scripts/demo.py)
- Docs de execução: [docs/RUN.md](../RUN.md)
