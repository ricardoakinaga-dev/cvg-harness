# 0059 - Sprint 31 - Contexto provider-aware em dispatch

## Objetivo

Levar a ergonomia provider-aware também para o `dispatch` externo, reutilizando contexto já derivado de `runtime-hooks.json` e `ci-result.json` sem acoplar o harness ao executor final.

## Nota histórica

Este documento foi sucedido pela trilha operacional consolidada em `docs/0060-sprint-31-contexto-provider-no-dispatch.md` e pelo fechamento causal em `docs/0061-sprint-33-contexto-causal-no-dispatch-concluido.md`. O texto abaixo permanece como histórico da etapa intermediária.

## Estado de partida

Após a Sprint 30:
- `cvg runtime` já aceitava atalhos de contexto por provider
- `runtime-hooks.json` e `ci-result.json` já preservavam `provider`, `raw_context` e `resolved_context`
- o gap restante estava no handoff externo: `dispatch` ainda era cego ao contexto derivado e não explicitava lacunas de contexto no plano externo

## Item único

### Dispatch com contexto derivado e requisitos explícitos

Tornar `dispatch` capaz de herdar contexto de `runtime/ci_result`, aceitar atalhos explícitos da CLI e persistir um plano externo com hints e requisitos mínimos.

Resultado esperado:
- `cvg dispatch` aceita `--context-json`, `--repository`, `--ci-run-id`, `--ci-api`, `--ci-url` e `--ci-status`
- `external-dispatch-plan.json` passa a registrar `provider`, `context`, `context_sources`, `context_hints`, `required_context`, `missing_context_hints`, `missing_required_context` e `available_context_keys`
- `dispatch` deriva contexto de `runtime-hooks.json` e `ci-result.json` quando existirem
- execução explícita (`--execute`) falha se o adapter exigir contexto obrigatório ausente
- `inspect` e a saída humana do `dispatch` passam a mostrar a proveniência e as lacunas de contexto

Arquivos-alvo:
- `src/cvg_harness/auto_runtime/external_executor.py`
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `tests/test_operator_cli.py`
- `docs/0007-contratos-dos-artefatos.md`
- `README.md`

## Critérios de saída

- adapters externos deixam de ser caixas-pretas no plano operacional
- `dispatch` reaproveita contexto real já observado pelo operador
- a execução explícita continua opt-in e segura
- o contrato do plano externo vira artefato canônico
- a suíte permanece verde

## Fechamento

Entrega concluída com contexto provider-aware em `dispatch`:
- `cvg dispatch` agora aceita atalhos explícitos de contexto, como `runtime`
- o operador herda contexto de `runtime-hooks.json` e `ci-result.json` quando eles existem
- `external-dispatch-plan.json` virou sidecar canônico com provider, contexto resolvido, fontes e lacunas
- `inspect` passou a expor melhor a causalidade de execução externa
- execução real por adapter continua opt-in e bloqueia quando faltar contexto obrigatório

Validação executada nesta rodada:
- `pytest -q tests/test_operator_cli.py tests/test_runtime.py` → `56 passed`
- `pytest -q` → `261 passed`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`
- `python3 -m cvg_harness dispatch --help` → flags provider-aware expostas

Encadeamento:
- próximo ciclo incremental deve consolidar adapters mais reais por provider no registry ou formalizar handoff enriquecido por capability, sem transformar o harness no executor final
