# Diagrams — conventions and rendering

This folder contains textual diagram sources (Mermaid) used as the canonical "source of truth" for architecture and experiments.

Why textual diagrams?
- They are diffable and reviewable in Git (PRs), enabling evolution tracking.
- They can be rendered locally (VSCode Mermaid preview) or in CI (Mermaid CLI `mmdc`).

Structure & naming
- `01_use_cases.mmd` — use case flows and actor interactions
- `02_state_machine.mmd` — job lifecycle state machine
- `03_uml_templates.mmd` — class and sequence diagram templates
- `artifacts/` — optional rendered outputs (SVG/PNG). Prefer not to commit large binaries.

File header (recommended)
```
%%
Author: Jeferson Oliveira de Sousa
Purpose: short description
Status: draft|reviewed|final
Date: YYYY-MM-DD
Reference: issue/ID
%%
```

Render locally
- VSCode: open file and use Mermaid preview extension.
- Mermaid CLI (Node):

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i 02_state_machine.mmd -o 02_state_machine.svg
```

CI suggestion
- Add a lightweight GitHub Action that runs `mmdc` for `.mmd` files changed in PRs and uploads rendered SVGs as artifacts or comments.

Best practices
- Keep diagrams small and focused (one responsibility per file).
- Prefer SVG output for clarity and scalability.
- Keep experimental/private variants in `private_docs/` or `.vscode/` and do not commit them.
