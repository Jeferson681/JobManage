# Decisions index and ADRs

This file is an **index** of project decisions.

Rule of thumb:

- Significant decisions (architecture/semantics) become ADRs under `docs/adr/`.
- This file links to ADRs and may record smaller decisions (tooling, conventions).

## Accepted ADRs

- [DB as queue (source of truth)](adr/0001-db-as-queue.md)
- [Retry policy (exponential + full jitter)](adr/0002-retry-policy.md)
- [Cooperative cancellation (best-effort)](adr/0003-cancel-semantics.md)

## Conventions and smaller decisions

- Language: primary documentation lives under `docs/` (root README is an overview + links).
- Minimal observability: JSON logs + `/health`, `/ready`, `/metrics` endpoints.
- CI: minimum coverage 90% in the test workflow.

## Template (for new ADRs)

Use the same format as files under `docs/adr/`.
