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
- Local-only developer artifacts (kept out of the repository and excluded by `.gitignore`).

If you believe a direct `sqlite3.connect` is necessary outside these locations, request an exception by opening an issue using the Exception Request template (choose "Exception request" when creating a new issue) and include:

- A justification describing why the storage layer cannot be used.
- The proposed file(s) and their intended lifetime (short-lived demo, long-term code, etc.).
- Any mitigations (e.g., explicit connection close, use of temporary directories, or test-only flags).

Maintainers will review exception requests and either approve, request changes, or suggest alternative approaches. Small, short-lived demos are more likely to be approved when documented clearly.

Vendorizing third-party tooling for CI
-----------------------------------

For stability of CI runs we may pin scanner binaries (e.g., TruffleHog). We prefer not to commit binaries directly when possible. The repository includes the following helpers:

- `tools/trufflehog.sha256`: a file containing the expected SHA256 hex for the pinned trufflehog tarball. Place the checksum here to enable CI verification.
- `scripts/fetch_trufflehog_checksum.py`: convenience script to fetch a release tarball and populate `tools/trufflehog.sha256` with the checksum.
- `scripts/vendor_trufflehog.py`: optional helper to download, verify and extract the trufflehog tarball into `tools/` if you prefer to vendor the binary.

Workflows prefer to download the pinned tarball and verify its SHA256 against `tools/trufflehog.sha256`. If the checksum file is absent the workflows fall back to installing `trufflehog` via `pip`. See `.github/workflows/ci-secrets-scan.yml` for details.
