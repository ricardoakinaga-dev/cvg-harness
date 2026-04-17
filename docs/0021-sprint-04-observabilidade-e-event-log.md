# 0021. Sprint 04 - Observabilidade e rastreabilidade operacional

## Objetivo
Consolidar a qualidade da observabilidade sem alterar o comportamento funcional já aprovado, com foco em event log e rastreabilidade operacional.

## Estado de partida
- Projeto aprovado após Sprint 02 e consolidado na Sprint 03.
- As implementações de fluxo, gates e release estão funcionais.
- Existe divergência de rastreabilidade operacional: o fluxo emite menos eventos canônicos de governança de falha/sucesso do que o contrato de trilha documenta.
- O contrato de observabilidade (`docs/0010-progress-ledger-e-event-log.md`) ainda não está 100% refletido no código atual sem abrir revisão de produto.

### Escopo incremental
- Não reabrir decisões estruturais já aprovadas nas Sprints 02/03 (arquitetura de fluxo, PRs e contratos centrais).
- Limitar a execução a ajustes de observabilidade e rastreabilidade.
- Não alterar semântica de aprovação/rejeição de fluxo neste ciclo.

## Itens desta sprint

### 1. Padronizar eventos de decisão de avaliação
**Status:** `done`

Objetivo: manter o modelo atual (sem mudança de lógica de aprovação) e alinhar rastreabilidade.

Alvo:
- Em `evaluate_sprint`, emitir também o evento canônico `evaluation_failed` quando houver falha e manter `sprint_failed` para continuidade.
- Em `evaluate_sprint`, manter emissão explícita de `evaluation_passed` em aprovação, com `sprint_approved` como evento legado.

Arquivos alvo:
- `src/cvg_harness/flow.py`
- `src/cvg_harness/types.py` (se necessário, para tipos/events canônicos)

Critério de saída:
- `event-log.jsonl` registra evento de decisão da avaliação em ambos os eixos, com metadados mínimos de fase/round.
- Métricas baseadas em eventos passam a refletir o estado de avaliação sem depender de inferência ambígua do log.

### 2. Alinhar catálogo de eventos com o observado na prática
**Status:** `done`

Objetivo: reduzir ambiguidade entre documentação de observabilidade e implementação.

Alvo:
- Revisar e reconciliar o catálogo de eventos canônicos com os eventos efetivamente emitidos.
- Incluir no contrato apenas eventos produzidos pelo fluxo atual; mover eventos não emitidos para “futuro” com data de implantação definida.
- Atualizar mapeamento de fases/gates se necessário para o ciclo real.

Arquivos alvo:
- `docs/0010-progress-ledger-e-event-log.md`
- `src/cvg_harness/types.py`
- `src/cvg_harness/ledger/event_log.py`

Critério de saída:
- documento de trilha e enum/tipo de eventos são consistentes entre si.
- não há evento “esperado” que não apareça por fluxo real sem nota de exceção.

### 3. Melhorar visibilidade de decisões de fallback e waiver no log
**Status:** `done`

Objetivo: manter rastreabilidade de decisões operacionais sem mudar semântica de fallback.

Alvo:
- Confirmar e padronizar quais decisões devem estar no event log (`waiver_granted`, `release_rejected`, `replan_requested`) e como são registradas.
- Garantir que dashboards/consumidores usem essas entradas com consistência.

Arquivos alvo:
- `src/cvg_harness/flow.py`
- `src/cvg_harness/fallback/fallback_policy.py`
- `src/cvg_harness/dashboard/dashboards.py`
- `tests/test_pr04_gates_fallback.py`

Critério de saída:
- decisão operacional relevante aparece em trilha auditável padronizada.
- `dashboard` e agregações podem explicar a causa de bloqueio/replanejamento via evento.

## Arquivos alvo geral
- `src/cvg_harness/flow.py`
- `src/cvg_harness/types.py`
- `src/cvg_harness/ledger/event_log.py`
- `src/cvg_harness/fallback/fallback_policy.py`
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `src/cvg_harness/dashboard/dashboards.py`
- `docs/0010-progress-ledger-e-event-log.md`
- `tests/test_pr04_gates_fallback.py`
- `tests/test_progress.py`

## Critérios de saída
- Event log permanece canônico e alinhado com a documentação de observabilidade.
- Não houve alteração de comportamento funcional de aprovação/rejeição dos fluxos existentes.
- Métricas e dashboard deixam de depender de interpretação frágil de eventos não emitidos.
- Todos os testes de contrato/documentação de sprint 04 passam conforme previsto.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "demand_received|research_started|evaluation_failed|evaluation_passed|drift_clean|release_rejected|waiver_granted|event log|event log" docs README.md examples tests src/cvg_harness -g "!**/__pycache__/**"
```

## Encerramento
**Sprint 04 concluída — 2026-04-16.**

Encerramento:
- ✅ Item 1: `evaluation_failed` e `evaluation_passed` emitidos explicitamente na trilha do evento de avaliação.
- ✅ Item 2: catálogo de eventos em `docs/0010`, `types.py` e `event_log.py` alinhados ao tráfego real do fluxo.
- ✅ Item 3: decisões de fallback e waiver rastreadas em evento (`evaluation_failed`, `sprint_failed`, `replan_requested`, `waiver_granted`).

Itens previstos: 3
- [ ] Padronizar eventos de decisão de avaliação
- [ ] Alinhar catálogo de eventos com trilha real
- [ ] Visibilidade de fallback/waiver no evento log

## Fechamento esperado
- 1 a 3 itens concluídos sem risco de reabrir aprovação.
- `docs/0021` pode ser executado diretamente por um agente com leitura de `src/cvg_harness/flow.py`, `src/cvg_harness/types.py`, `src/cvg_harness/ledger/event_log.py` e `docs/0010`.
- Não há mudanças de comportamento funcional (apenas rastreabilidade e precisão documental).
