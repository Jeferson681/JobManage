JobManager

Backend service para gerenciamento e execução de jobs.

Status: levantamento e design — estrutura inicial apenas.

## Dev environment

### Install (Windows)

```powershell
# create/activate venv (example)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# tooling
python -m pip install -r requirements-dev.txt

# pre-commit
python -m pre_commit install
```

### Quality commands

```powershell
python -m black .
python -m isort .
python -m ruff check .
python -m mypy src
python -m pytest
python -m pytest --cov=src --cov-report=term-missing --cov-report=xml
python -m pre_commit run --all-files
```
