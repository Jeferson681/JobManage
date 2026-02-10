Title: Retry policy and backoff with full jitter
Status: Accepted
Date: 2026-02-10

Context
-------
Jobs may fail transiently (network calls, downstream services). A retry policy reduces manual intervention but must avoid thundering-herd retries.

Decision
--------
Use an exponential backoff with full jitter (delay = uniform(0, min(max_delay, base ** attempt))). Track `attempt` and `max_attempts` on the job row. Failed, retryable jobs are marked `FAILED_RETRYABLE` with a `next_run_at` timestamp.

Consequences
------------
- Pros:
  - Stochastic spreading reduces synchronized retries and downstream load spikes.
  - Simple to implement and reason about in code/tests.
- Cons:
  - Jitter makes exact timing non-deterministic; tests should patch RNG for determinism when needed.
  - Requires careful monitoring of `FAILED_RETRYABLE` and DLQ considerations for permanently failing jobs.

Alternatives considered
---------------------
- Fixed backoff: simpler, but more predictable and prone to coordinated retry spikes.
- Full queue-based DLQ approach: move permanent failures to a DLQ for manual inspection; can be layered on top of current approach.

Notes
-----
Implement metrics and alerts for growing `FAILED_RETRYABLE` counts, and a separate process or API to inspect/purge DLQ items when `attempt >= max_attempts`.
