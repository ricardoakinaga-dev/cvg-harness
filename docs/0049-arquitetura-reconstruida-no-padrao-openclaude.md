# 0049 — Arquitetura Reconstruída no Padrão OpenClaude

## Princípios incorporados

- modo único (`harness`) com interface conversacional,
- frontend desacoplado do core (engine de negócio),
- seleção automática de rota/subagente,
- setup inicial guiado,
- separação de camadas para futura headless.

## Estrutura adotada

- `app/` : sessão, fluxo e orquestração conversacional.
- `session/` : estado de sessão do usuário.
- `routing/` : decisão de intenção.
- `providers/` : abstração e adaptação de LLMs.
- `workspace/` : gerenciamento de estado local `.harness`.
- `runtime/` : operações de ambiente (futuro headless).
- `cli/harness.py` : front-end principal.
- `cli/cli.py` : comandos técnicos antigos preservados.
- `operator/` : engine de governança preservada.

## Adaptação de identidade

- Mantive nomenclatura e contratos de governance existentes (`run`, `status`, `continue`, `replan`, `events`, `metrics`).
- O padrão de layout e separação do loop principal segue a mentalidade de “front-agent” sem virar clone textual.
