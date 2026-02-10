# RUN — Como rodar e reproduzir cenários

Objetivo: passos **reprodutíveis** para executar a API e o worker localmente, aplicar migrações e coletar evidências (artefatos) do laboratório.

Referências:

- Hub técnico: [docs/README-TECH.md](README-TECH.md)
- Contrato da API: [docs/API_CONTRACT.md](API_CONTRACT.md)
- Artefatos/Evidências: [docs/artifacts/README.md](artifacts/README.md)

## 1) Pré-requisitos

- Git
- Python 3.11+ (CI usa 3.11; local pode ser mais novo)
- (Opcional) Make

Observação: Docker/Compose ainda não fazem parte do repositório. Esta seção fica como placeholder para quando adicionarmos `Dockerfile` e `docker-compose.yml`.

## 2) Ambiente local (venv) — Windows / PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e '.[dev]'
```

Registro de versão (opcional, evidência):

```powershell
python --version
python -m pip freeze > docs\artifacts\pinned-requirements.txt
```

## 3) Banco de dados (SQLite) e variável de ambiente

Por padrão o projeto usa SQLite em memória se `JOBMANAGER_DB` não estiver definido. Para um DB persistente:

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
```

## 4) Migrações (Alembic)

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -m alembic upgrade head
```

Nota: o Alembic aceita `JOBMANAGER_DB` como caminho (ex.: `C:\...\jobmanager.db`) ou URL SQLite (`sqlite:///...`).

## 5) Subir a API

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -m uvicorn jobmanager.api.app:app --reload --port 8000
```

Endpoints úteis:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/ready`
- `GET http://localhost:8000/metrics`

## 6) Rodar o worker

Em outro terminal:

```powershell
.venv\Scripts\Activate.ps1
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -c "from jobmanager.worker.runner import run; run(worker_id='worker-1', poll_interval=1.0)"
```

Rodar apenas 1 iteração (útil para depuração):

```powershell
python -c "from jobmanager.worker.runner import run_once; print(run_once(worker_id='worker-1'))"
```

## 7) Reproduzir cenários (experimentos)

### 7.1 Demo rápida (recomendado)

```powershell
.venv\Scripts\Activate.ps1
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python scripts\demo.py | Tee-Object -FilePath docs\artifacts\runs\demo_stdout.log
```

### 7.2 Criar job via API (cURL)

```bash
curl -X POST http://localhost:8000/jobs \
	-H 'Content-Type: application/json' \
	-H 'Idempotency-Key: demo-1' \
	-d '{"job_type":"demo","payload":{"x":1},"max_attempts":3}'
```

## 8) Checagens (qualidade e testes)

```powershell
python -m pre_commit run --all-files
python -m pytest -q
```

Cobertura (evidência):

```powershell
python -m pytest --cov=src --cov-report=term-missing --cov-report=xml
```

## 9) Placeholders (Docker)

Quando existirem `Dockerfile` e `docker-compose.yml`, documentar aqui:

- como buildar e rodar
- como configurar `JOBMANAGER_DB`
- como coletar logs/artefatos do compose
