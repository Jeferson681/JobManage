# RUN — Local execution and scenarios

This guide provides **reproducible** steps to run the API and worker locally, apply migrations, and capture execution artifacts (logs, metrics, outputs) for inspection.

References:

- Tech hub: [docs/README-TECH.md](README-TECH.md)
- API contract: [docs/API_CONTRACT.md](API_CONTRACT.md)
- Artifacts: [docs/artifacts/README.md](artifacts/README.md)

## 1) Prerequisites

- Git
- Python 3.11+ (CI uses 3.11; local can be newer)
- (Optional) Make

Note: Docker/Compose are not part of this repository yet. This section is reserved for when `Dockerfile` and `docker-compose.yml` exist.

## 2) Local environment (venv) — Windows / PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e '.[dev]'
```

Version record (optional, as evidence):

```powershell
python --version
python -m pip freeze > docs\artifacts\pinned-requirements.txt
```

## 3) Database (SQLite) and environment variable

By default the project uses in-memory SQLite when `JOBMANAGER_DB` is not set. For a persistent DB:

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
```

## 4) Migrations (Alembic)

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -m alembic upgrade head
```

Note: Alembic accepts `JOBMANAGER_DB` as a path (e.g. `C:\...\jobmanager.db`) or as a SQLite URL (`sqlite:///...`).

## 5) Start the API

```powershell
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -m uvicorn jobmanager.api.app:app --reload --port 8000
```

Useful endpoints:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/ready`
- `GET http://localhost:8000/metrics`

## 6) Run the worker

Em outro terminal:

```powershell
.venv\Scripts\Activate.ps1
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python -c "from jobmanager.worker.runner import run; run(worker_id='worker-1', poll_interval=1.0)"
```

Run a single iteration (useful for debugging):

```powershell
python -c "from jobmanager.worker.runner import run_once; print(run_once(worker_id='worker-1'))"
```

## 7) Reproduce scenarios

### 7.1 Quick demo (example)

```powershell
.venv\Scripts\Activate.ps1
$Env:JOBMANAGER_DB = "$PWD\jobmanager.db"
python scripts\demo.py | Tee-Object -FilePath docs\artifacts\runs\demo_stdout.log
```

Note: `scripts\demo.py` writes directly to the SQLite file you pass via `--db` (default: `./demo.db`).
If you want `GET /metrics` to reflect the demo state, start the API with `JOBMANAGER_DB` pointing to the same file.

### 7.2 Create a job via API (cURL)

```bash
curl -X POST http://localhost:8000/jobs \
	-H 'Content-Type: application/json' \
	-H 'Idempotency-Key: demo-1' \
	-d '{"job_type":"demo","payload":{"x":1},"max_attempts":3}'
```

## 8) Checks (quality and tests)

```powershell
python -m pre_commit run --all-files
python -m pytest -q
```

Coverage (evidence):

```powershell
python -m pytest --cov=src --cov-report=term-missing --cov-report=xml
```

## 9) Docker (reserved section)

When `Dockerfile` and `docker-compose.yml` exist, document here:

- how to build and run
- how to configure `JOBMANAGER_DB`
- how to collect logs/artifacts from compose

---

## 10) CI artifacts workflow (how to reproduce locally)

This repository includes a CI workflow that generates demo artifacts under `docs/artifacts/assist_run`.

Reproduce locally (Linux/macOS shell):

```bash
python -m pip install -e '.[dev]'
rm -rf docs/artifacts/assist_run
mkdir -p docs/artifacts/assist_run
python scripts/demo.py --db docs/artifacts/assist_run/demo.db --iterations 12 > docs/artifacts/assist_run/demo_output.txt
# Use the public helper in `scripts/` when available. If you keep a local,
# private helper for artifact generation, run it locally outside the repo.
python scripts/generate_artifacts.py --db docs/artifacts/assist_run/demo.db --out docs/artifacts/assist_run
python -c "import json; print(json.load(open('docs/artifacts/assist_run/metrics.txt')))"
```

Reproduce locally (Windows / PowerShell):

```powershell
python -m pip install -e '.[dev]'
Remove-Item -Recurse -Force docs\artifacts\assist_run -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force docs\artifacts\assist_run | Out-Null
python scripts\demo.py --db docs\artifacts\assist_run\demo.db --iterations 12 | Tee-Object -FilePath docs\artifacts\assist_run\demo_output.txt
# Prefer the public helper in `scripts/`. If you use a private/local helper,
# run it locally (do not commit private helpers to the remote repository).
python scripts\generate_artifacts.py --db docs\artifacts\assist_run\demo.db --out docs\artifacts\assist_run
python -c "import json; print(json.load(open('docs/artifacts/assist_run/metrics.txt', encoding='utf-8')))"
```
