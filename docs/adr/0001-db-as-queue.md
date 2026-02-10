Title: Use the primary application database as the job queue
Status: Accepted
Date: 2026-02-10

Context
-------
We need a durable queue to persist jobs, their attempts, and state transitions. Options include using the primary relational database (SQLite in dev, Postgres in prod), an external queue (RabbitMQ, SQS), or a dedicated job table backed by a separate database.

Decision
--------
We will use the primary relational database as the job queue, implementing a `jobs` table with explicit states, `locked_until`, and `next_run_at` for backoff scheduling.

Consequences
------------
- Pros:
  - Simpler operational model (no additional infra required for dev and small deployments).
  - Strong consistency and easy ad-hoc queries for debugging and runbook actions.
  - Easier to migrate schema using Alembic revisions.
- Cons:
  - Scalability limits compared to purpose-built queue systems under very high throughput.
  - Requires careful row-level locking or atomic updates to avoid double-processing; this is managed via `reserve_next` update semantics.

Alternatives considered
---------------------
- External queue (RabbitMQ/SQS): better at scale and decoupling, but adds operational complexity and cost.
- Dedicated NoSQL queue (Redis streams): performant but trading durability model and introduces another datastore.

Notes
-----
For production, favour a robust RDBMS (Postgres) and monitor queue-related metrics; revisit if throughput or latency demands grow.
