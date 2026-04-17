# 0040. Sprint 17 - Observabilidade causal de gates

## Objetivo
Executar uma rodada curta para aprofundar a observabilidade P2 do `cvg-harness`, tornando a trilha de gates, rounds e bloqueios mais causal e mais legível operacionalmente, sem reabrir planning, release, guardian/drift ou métricas canônicas já estabilizadas.

## Estado de partida
- O projeto segue aprovado e estável após a Sprint 16.
- Auditoria mais recente em `docs/0039-relatorio-de-auditoria-pos-sprint-16.md` elevou a nota global para `89/100`.
- Os gaps mais defensáveis agora estão em:
  - `Capacidades P2 de observabilidade/analytics` -> `81/100`
  - `Evaluator / QA Gate` -> `78/100`
  - `Dashboard/sidecars analíticos` ainda pouco explorados no fluxo real
- O estado validado antes desta sprint é:
  - `pytest -q` -> `207/207`
  - `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`

## Foco da sprint
Atacar apenas causalidade de gates, rounds e bloqueios no fluxo real e em seus sidecars operacionais.

## Itens do sprint

### 1. Tornar eventos de gate mais causais
**Status:** `done`

Arquivos alvo:
- `src/cvg_harness/flow.py`
- `src/cvg_harness/ledger/event_log.py`
- `tests/test_pr03_flow_orchestrator.py`

Mudanças esperadas:
- enriquecer eventos de gate com motivo, artefato de origem e transição de estado;
- reduzir eventos genéricos quando já há decisão formal persistida;
- melhorar a legibilidade para consumo por métricas e dashboard.

Resultado desta rodada:
- `_evaluate_and_save_gate()` passou a registrar eventos causais por gate com `state`, `previous_state`, `blockers` e `source_artifact_ref`;
- o event log agora distingue `gate_approved`, `gate_rejected` e `gate_waived` no caminho real do fluxo;
- a cobertura prova causalidade de gate em `GATE_0`, `GATE_6` e `GATE_8`;
- o registro canônico de eventos foi ampliado sem substituir os eventos de fase já úteis para leitura humana.

### 2. Expor rounds e blockers com semântica mais forte
**Status:** `done`

Arquivos alvo:
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `src/cvg_harness/dashboard/dashboards.py`
- `tests/test_agents_extended.py`
- `tests/test_progress.py`

Mudanças esperadas:
- diferenciar retry, replan, waiver e blocker estrutural nas métricas;
- refletir isso nos sidecars operacionais e dashboard.

Resultado desta rodada:
- `MetricsAggregator` passou a expor `retry_rounds`, `replan_events`, `waiver_events` e `structural_blockers`;
- `Dashboard` agora enriquece `metrics_summary` com essa semântica mesmo quando os dados vêm apenas do `progress ledger` + `event log`;
- a cobertura foi ajustada para encadear `delivery-metrics.json` e `dashboard.json` persistidos a partir de eventos reais.

### 3. Consolidar cobertura e trilha documental
**Status:** `done`

Arquivos alvo:
- `docs/0039-relatorio-de-auditoria-pos-sprint-16.md`
- `tests/test_pr03_flow_orchestrator.py`
- `tests/test_agents_extended.py`

Mudanças esperadas:
- registrar o ganho de observabilidade de forma auditável;
- deixar a próxima auditoria capaz de recalibrar P2 com evidência objetiva.

Resultado desta rodada:
- a trilha documental passou a registrar a semântica adicional de `retry_rounds`, `replan_events`, `waiver_events` e `structural_blockers`;
- `docs/0039-relatorio-de-auditoria-pos-sprint-16.md` permanece histórico, mas agora aponta mais claramente para a linha de observabilidade que foi consolidada na Sprint 17;
- a cobertura adicionada em `tests/test_agents_extended.py` protege o contrato dos sidecars operacionais sem mexer no núcleo aprovado.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
pytest -q tests/test_pr03_flow_orchestrator.py tests/test_agents_extended.py tests/test_progress.py -rA
rg -n "gate_|blocker|waiver|retry|replan|dashboard|metrics" src docs tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- o fluxo passa a expor causalidade mais clara de gates e bloqueios;
- rounds e blockers ficam legíveis em métricas e sidecars operacionais;
- a cobertura e a trilha documental deixam esse avanço explícito;
- o escopo permanece incremental, sem reabrir os blocos já estabilizados.

## Validação executada
- Focada item 1: `pytest -q tests/test_pr03_flow_orchestrator.py tests/test_progress.py` -> `30/30`.
- Completa: `pytest -q -rA` -> `207 passed`.
- Coleta: `pytest --collect-only -q` -> `207 tests collected`.
- Demo: `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`.
