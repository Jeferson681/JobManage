# Contributing

Thanks for contributing. This project is primarily a private learning lab, but contributions and improvements are welcome by invitation.

If you work on this repository:

- Follow code style and checks: `black`, `isort`, `ruff`, `mypy`.
- Run pre-commit hooks locally: `.venv\Scripts\python.exe -m pre_commit run --all-files`.
- Write tests for new logic and keep them small and focused.
- For documentation or design changes, update the appropriate file under `docs/` and add an ADR to `docs/DECISIONS.md` when applicable.

PR process (suggested):
- Open a PR with a clear summary and related issue or decision.
- Keep commits small and focused; prefer a single topic per branch.

Note: This project is authored by Jeferson Oliveira de Sousa. Contact via email before submitting major changes.

## Exceptions: usage of `sqlite3.connect`

We aim to centralize direct database connections inside the storage layer to improve testability and reduce accidental file/connection leaks.

Allowed locations for direct `sqlite3.connect` usage:

- `src/jobmanager/storage/` — the canonical storage layer for the project.
- `tests/` — test fixtures, demos and temporary examples.
- `tools/` and `scripts/` — helper scripts and local developer utilities.
- `private_docs/` — intentionally noisy or private artifacts (allowlisted for scanners).

If you believe a direct `sqlite3.connect` is necessary outside these locations, request an exception by opening an issue using the Exception Request template (choose "Exception request" when creating a new issue) and include:

- A justification describing why the storage layer cannot be used.
- The proposed file(s) and their intended lifetime (short-lived demo, long-term code, etc.).
- Any mitigations (e.g., explicit connection close, use of temporary directories, or test-only flags).

Maintainers will review exception requests and either approve, request changes, or suggest alternative approaches. Small, short-lived demos are more likely to be approved when documented clearly.
