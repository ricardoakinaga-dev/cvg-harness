# 0046 — Roteador de Subagentes e Seleção Automática de Tools

## Objetivo
Decidir automaticamente o que executar a partir de intenção em português, sem comandos técnicos no loop principal.

## Roteador de intenção
`routing/router.py` classifica entradas em:
- `new_demand`
- `status`, `inspect`, `history`, `continue`, `replan`, `reason`, `resume`, `summary`, `help`, `doctor`, `debug`, `exit`

## Roteador de engine
`routing/engine_router.py` constrói:
- `mode` (`FAST` ou `ENTERPRISE`)
- `tools` (`filesystem`, `shell`, `planning`, `subagent`, `context_memory`)
- `subagents` na pipeline (research, prd, spec_builder, spec_linter, sprint_planner, guardian, evaluator, drift_detector, release_readiness, replan_coordinator, metrics_aggregator)
- modelo sugerido por modo
- `require_human_confirmation`

## Execução
`FrontAgent._new_demand()` chama `OperatorService.start_run()` e então `operator` + `SubagentTool` para cada etapa da pipeline.

## Quando pedir intervenção humana
- confirmação da sprint inicial (`approve_sprint`)
- run bloqueada por guard/erro
- replanejamento explícito

## Estado da execução
O sistema registra:
- plano persistido (`.harness/runs/<id>/plan.json`)
- eventos de execução (`.harness/runs/<id>/event-log.jsonl`)
- artefatos, reports e causalidade por run.
