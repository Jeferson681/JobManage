# Developer commands (local parity with CI).

PY ?= python

.PHONY: help
help:
	@echo "Targets: format | format-check | lint | typecheck | test | coverage | precommit | check"

.PHONY: format
format:
	$(PY) -m black .
	$(PY) -m isort .

.PHONY: format-check
format-check:
	$(PY) -m black --check .
	$(PY) -m isort --check-only .

.PHONY: lint
lint:
	$(PY) -m ruff check .

.PHONY: typecheck
typecheck:
	$(PY) -m mypy src

.PHONY: test
test:
	$(PY) -m pytest

.PHONY: coverage
coverage:
	$(PY) -m pytest --cov=src --cov-report=term-missing --cov-report=xml

.PHONY: precommit
precommit:
	$(PY) -m pre_commit run --all-files

.PHONY: check
check: format-check lint typecheck test
