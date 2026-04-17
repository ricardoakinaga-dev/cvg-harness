# 0044 — Agente de Terminal Prompt-First

## Objetivo

`harness` é o modo principal. O usuário conversa em linguagem natural no terminal, sem expor comandos internos.

Exemplos:

- `harness`
- `> criar módulo de permissões por setor`
- `> revisar este projeto e montar um plano seguro para modularizar a agenda`
- `> adicionar autenticação OAuth2 com Google`

## Fluxo de alto nível

1. O agente detecta o workspace atual (`pwd`).
2. Carrega configuração global/local de provider e estado.
3. Inicia onboarding quando necessário.
4. Entra no loop conversacional.
5. Classifica demanda e dispara engine (`FAST`/`ENTERPRISE`).
6. Executa o pipeline atual de governança (`research`, `PRD`, `SPEC`, `spec lint`, `sprint`, `evaluator`, `guard`, `drift`, `release readiness`).
7. Entrega uma resposta de estado e próximos passos.

## Diferença para o modo técnico

- O modo técnico permanece disponível, mas em namespace separado:
  - `harness debug <comando-antigo>`
- Exemplos de comandos técnicos antigos: `classify`, `lint`, `guard`, `drift`, `progress`, `event`, `handoff`, `template`.
- O usuário comum não precisa invocar estes nomes para fluxo normal.

## Resposta esperada do loop

O agente precisa manter histórico e estado da sessão e permitir:

- inspeção (`status`, `inspect`, `continue`, `retome`),
- justificativa (`por que você escolheu enterprise?`),
- replanejamento (`replaneje com menos risco`),
- encerramento e retorno ao estado.
