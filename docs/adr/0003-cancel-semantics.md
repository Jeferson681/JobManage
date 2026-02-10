Title: Cooperative cancellation semantics for running jobs
Status: Accepted
Date: 2026-02-10

Context
-------
Users need a way to request cancellation of enqueued or running jobs. Immediate forced termination is unsafe for many workloads; cooperative cancellation allows jobs to observe cancellation requests.

Decision
--------
Support a `CANCEL_REQUESTED` state that a worker checks immediately after reservation. If present, the worker marks the job `CANCELED` and clears the lock. Cancel requests on queued jobs update status to `CANCEL_REQUESTED` so the next worker or the current worker can honor it.

Consequences
------------
- Pros:
  - Safe cooperative behavior; avoids forcing abrupt termination of in-flight work.
  - Simple to implement and test.
- Cons:
  - Long-running tasks must poll or check for cancel semantics internally if they perform lengthy processing beyond this scaffold's immediate succeed/failed paths.

Alternatives considered
---------------------
- Forced termination: send a signal to worker processes to terminate — more complex and riskier for stateful work.
- External cancellation coordination (webhooks, callbacks): adds complexity and eventual consistency issues.

Notes
-----
Document how application-specific long-running tasks should check `CANCEL_REQUESTED` and provide a pattern/library helper if needed.
