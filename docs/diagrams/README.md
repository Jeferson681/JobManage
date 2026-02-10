# Diagramas — convenções e como renderizar

Este diretório contém diagramas em Mermaid, usados como “source of truth” para a arquitetura e para o laboratório.

Observação: neste repositório os diagramas estão em arquivos `.md` com blocos ` ```mermaid `.

## Arquivos

- [docs/diagrams/architecture.md](architecture.md)
- [docs/diagrams/01_use_cases.md](01_use_cases.md)
- [docs/diagrams/02_state_machine.md](02_state_machine.md)
- [docs/diagrams/03_uml_templates.md](03_uml_templates.md)

## Visualizar localmente

- VS Code: abra o arquivo e use uma extensão de preview Mermaid (ou preview Markdown que suporte Mermaid).

## Renderizar SVG/PNG (opcional)

Se você quiser gerar imagens para evidências/portfólio:

```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i docs/diagrams/02_state_machine.md -o docs/artifacts/diagrams/02_state_machine.svg
```

Placeholders para armazenar esse tipo de evidência: [docs/artifacts/README.md](../artifacts/README.md).
