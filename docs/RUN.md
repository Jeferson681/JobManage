# RUN — Reproducing experiments and running the system

Objetivo: passos reprodutíveis para executar a API e os workers, localmente e em container, e reproduzir experimentos do laboratório.

1) Pré-requisitos
- Git
- Python 3.10+
- Docker & Docker Compose (opcional, recomendado para reprodução)
- Make (opcional)

2) Ambiente reprodutível (venv)

Windows / PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

Registre as versões instaladas para referência:

```powershell
pip freeze > pinned-requirements.txt
```

3) Executando localmente (modo desenvolvimento)

- Rodar a API (ex.: FastAPI):

```powershell
uvicorn jobmanager.api:app --reload --port 8000
```

- Rodar worker (exemplo mínimo):

```powershell
python -m jobmanager.worker --config config.yml
```

Observação: ajuste os comandos acima ao entrypoint real do projeto.

4) Executando com Docker (reprodução confiável)

- Exemplo (assumindo `Dockerfile` e `docker-compose.yml` presentes):

```bash
docker compose up --build
```

- Para rodar somente um serviço:

```bash
docker compose up api
docker compose up worker
```

5) Reproduzindo experimentos (ex.: crash, retry, lease)

- Preparar dados de entrada (script `scripts/seed_jobs.py` ou curl POST)
- Executar cenário: iniciar API, criar N jobs, iniciar worker(s) com delay/limite de concorrência
- Para simular crash: matar processo do worker (`docker kill` ou `Ctrl+C`) e observar comportamento de lease/reativação
- Registrar resultados em `artifacts/` (logs, job-export.json) para análise comparável

6) Verificações e checagens

- Rodar linters/testes antes de experimento:

```powershell
pre-commit run --all-files
make test
```

- Coletar métricas/logs relevantes: `logs/` (arquivo) ou `stdout` estruturado com `job_id`.

7) Notas sobre segredos e configuração

- Use um arquivo `.env` local ou variáveis de ambiente. Nunca commit `.env`.
- Para Docker, forneça secrets via environment variables em `docker-compose.override.yml` ou um Vault.

8) Artefatos reprodutíveis

- Salve: `pinned-requirements.txt`, `docker-compose.yml`, `artifact/*.log`, `artifact/jobs-export.json`, e um `run-notes.md` com comandos exatos usados.

9) Exemplo rápido de sequência de comandos (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pre-commit run --all-files
uvicorn jobmanager.api:app --reload --port 8000 &
python scripts/seed_jobs.py
python -m jobmanager.worker
```

10) Próximos passos recomendados
- Criar `docker-compose.yml` com serviços: `api`, `worker`, `db` para reprodução completa.
- Criar scripts em `scripts/` para `seed_jobs.py` e `collect_artifacts.py`.
- Documentar experimentos esperados em `docs/experiments/` com checklist de passos e métricas a coletar.
