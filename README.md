# JobManager

> WIP — Private

JobManager é um laboratório técnico de backend para demonstrar um sistema de jobs assíncronos com workers, persistência auditável, políticas de retry/cancelamento e observabilidade básica.

Status: Work in progress (private). License: MIT.

## Começando (Windows)

Crie um ambiente virtual e instale dependências de desenvolvimento:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Comandos úteis:

```powershell
# format
black .
# isort (se necessário)
isort .
# lint
ruff check .
# typecheck
mypy src || true
# tests
pytest
# pre-commit
.venv\Scripts\python.exe -m pre_commit run --all-files
```

## Documento de levantamento

Interno: veja `private_docs/Documento_Levantamento_Direcionamento_Tecnico.md` para requisitos, decisões e contratos.

## Diagrams

Diagrama de arquitetura (rascunho local): `docs/diagrams/architecture.mmd` — mantido localmente enquanto estiver em draft.

## License

MIT — ver `LICENSE`.

## Contato

Jeferson Oliveira de Sousa — Jefersonoliveiradesousa681@gmail.com
