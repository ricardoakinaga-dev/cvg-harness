# 0060 - Sprint 31 - Contexto provider-aware no dispatch

## Objetivo

Levar a mesma resolução de contexto já aplicada ao runtime/CI para o `dispatch` externo, reduzindo o atrito do operador e mantendo o harness como orquestrador opt-in.

## Estado de partida

Após a Sprint 30:
- `runtime-profiles` já expunha `provider`, `required_context`, `example_contexts` e `command_examples`
- `OperatorService` já resolvia contexto por provider no runtime/CI
- `external-dispatch-plan.json` já carregava `provider`, `context_sources`, `required_context` e lacunas explícitas
- `cvg dispatch` já aceitava atalhos como `--repository`, `--ci-run-id`, `--ci-api`, `--ci-url` e `--ci-status`

O gap restante era a consistência documental e operacional do dispatch:
- o dispatch externo ainda estava descrito mais como handoff genérico do que como contexto provider-aware
- faltava alinhar o contrato e a UX a esse fluxo já presente no código

## Item do sprint

### Item único - dispatch provider-aware

Documentar e consolidar o dispatch externo com contexto resolvido por provider.

Resultado esperado:
- `cvg dispatch` aceita contexto explícito por flags e também `context-json`
- `external-dispatch-plan.json` registra contexto bruto, resolvido, fontes e lacunas
- o operador enxerga `provider`, `required_context` e `available_context_keys`
- os adapters conhecidos ficam mais legíveis para `manual-review`, `local-cli` e perfis provider-aware

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/auto_runtime/external_executor.py`
- `docs/0007-contratos-dos-artefatos.md`
- `README.md`

## Critérios de saída

- o dispatch deixa de ser apenas um handoff textual e passa a carregar contexto operacional explícito
- o contrato do plan de dispatch reflete o payload real do código
- a UX do operador fica coerente com runtime/CI provider-aware
- a suíte permanece verde

## Fechamento

Entrega documentada com dispatch provider-aware:
- `cvg dispatch` aceita os mesmos atalhos operacionais de contexto do runtime
- `external-dispatch-plan.json` registra `provider`, `context_sources`, `required_context`, `missing_required_context` e `available_context_keys`
- o contrato dos artefatos e o README foram alinhados ao payload real

Validação executada nesta rodada:
- `pytest -q` -> `253 passed`

Encadeamento:
- próximo ciclo incremental pode ampliar o catálogo de adapters reais ou aprofundar a execução externa efetiva para além do planejamento opt-in
