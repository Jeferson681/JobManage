# Technical Documentation

Purpose: central location for technical documentation: architecture, contracts, design decisions and runbooks.

Structure:
- `README-tech.md` (this file): index and navigation for tech docs.
- `DECISIONS.md`: decision records (ADR-style).
- `HANDOVER.md`: runbook / handover template.
- `diagrams/`: architecture and sequence diagrams.
- `private_docs/`: internal drafts and extended notes (kept local by policy).

Guidelines:
- Keep high-level rationale in `DECISIONS.md` (one decision per entry).
- Keep runnable instructions in `HANDOVER.md`.
- Do not duplicate long how-to content in the root `README.md` — link to the specific doc.

When updating docs:
- Add or update the appropriate document (DECISIONS/HANDOVER/diagrams).
- Reference the change in the commit message (e.g., `docs: add ADR for lease strategy`).
- For large changes, open a short PR summarizing the intent.
