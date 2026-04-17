# 0010. Progress ledger e event log

## Objetivo
Criar trilha viva, auditável e reprodutível da execução.

## `progress.json`
É o estado corrente do fluxo.

## Campos mínimos recomendados
```json
{
  "project": "cvg-harness",
  "feature": "string",
  "mode": "FAST|ENTERPRISE",
  "status": "in_progress",
  "currentGate": "GATE_4",
  "currentSprint": "SPRINT-001",
  "artifacts": {
    "classification": "v1",
    "prd": "v2",
    "spec": "v3"
  },
  "gates": {
    "GATE_0": "approved",
    "GATE_1": "approved",
    "GATE_2": "in_review"
  },
  "rounds": {
    "coder": 1,
    "evaluator": 0,
    "replan": 0
  },
  "blockers": [],
  "metrics": {
    "acceptancePassRate": 0.0,
    "estimatedCostUsd": 0.0
  }
}
```

## Regras do `progress.json`
- pode ser atualizado durante toda a execução
- nunca deve ocultar bloqueio aberto
- mudança de gate exige evento correspondente no log

## `event-log.jsonl`
É a trilha append-only dos eventos.

## Eventos mínimos
Fonte canônica: [src/cvg_harness/types.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/types.py:1).
`event_log.py` reusa essa lista canônica para evitar deriva entre contrato e runtime.

- `demand_received`
- `demand_classified`
- `research_started`
- `research_approved`
- `prd_approved`
- `spec_created`
- `spec_lint_failed`
- `spec_lint_passed`
- `sprint_started`
- `sprint_planned`
- `sprint_failed`
- `architecture_guard_failed`
- `architecture_guard_passed`
- `evaluation_failed`
- `evaluation_passed`
- `drift_detected`
- `drift_clean`
- `replan_requested`
- `sprint_approved`
- `release_approved`
- `release_rejected`
- `waiver_granted`

## Pontos de emissão
- `demand_received`: emitido pelo `FlowOrchestrator` no início de `classify()`, antes da classificação ser persistida.
- `research_started`: emitido pelo `FlowOrchestrator` no início de `run_research()`, antes de chamar o `ResearchAgent`.

## Formato recomendado do evento
```json
{"timestamp":"2026-04-16T12:00:00Z","event_type":"spec_lint_failed","actor":"spec-linter","artifact_ref":"spec.json@v3","metadata":{"blockingIssues":2}}
```

## Regras do event log
- append-only
- nenhum evento crítico pode ficar sem registro
- reprocessamento deve criar novo evento, não sobrescrever o anterior
- todo waiver relevante precisa virar evento

## Uso futuro
O event log deve ser a base para:
- analytics
- dashboard
- auditoria
- score por agente
- análise de gargalos
