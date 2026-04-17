# 0039. Sprint 17 - Scoring por agente canônico

## Objetivo
Fechar a frente P2 de `scoring por agente` com cálculo determinístico e contrato persistente, usando apenas o `event-log.jsonl` real e sem reabrir o fluxo aprovado.

## Estado de partida
- O projeto continua aprovado após a Sprint 16.
- `Architecture Guardian` e `Drift Detector` já foram endurecidos e validados.
- A camada de `agent_scoring` existe, mas ainda tinha lógica frágil para `needs_improvement` e cálculo pouco explícito de `rounds_avg` e custo estimado.
- Não havia cobertura de contrato para persistência do relatório de score por agente.

## Foco da sprint
Consertar o scoring por agente como métrica operacional P2, com cobertura curta e auditável.

## Itens da sprint

### 1. Corrigir e estabilizar o score por agente
**Status:** `done`

Objetivo:
- tornar o ranking por agente consistente e derivado de eventos reais;
- eliminar bug de seleção de `needs_improvement`;
- dar leitura mínima a `rounds_avg` e `estimated_cost_usd`.

Arquivos alvo:
- `src/cvg_harness/agent_scoring/agent_scores.py`
- `tests/test_agents_extended.py`

Mudanças esperadas:
- calcular `rounds_avg` com base em metadados de round quando existirem;
- manter fallback conservador quando o log não trouxer round explícito;
- calcular custo estimado de forma rastreável e estável;
- ordenar o ranking de forma determinística.

Critérios de saída:
- `top_performer` e `needs_improvement` refletem o log de eventos;
- o score continua serializável sem campos implícitos;
- o cálculo não depende de inferência externa ao workspace.

### 2. Cobrir persistência do relatório de scores
**Status:** `done`

Objetivo:
- provar que o relatório de score por agente pode ser salvo e recarregado sem perder coerência.

Arquivos alvo:
- `src/cvg_harness/agent_scoring/agent_scores.py`
- `tests/test_agents_extended.py`

Mudanças esperadas:
- validar `save_agent_scores` e `load_agent_scores`;
- garantir leitura do score persistido com objetos aninhados reconstruídos;
- registrar o comportamento com eventos reais mínimos.

Critérios de saída:
- o contrato do relatório fica exercitado por teste;
- a persistência preserva ranking, pass rate e score dos agentes.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "AgentScoring|AgentScoreReport|save_agent_scores|load_agent_scores|needs_improvement|rounds_avg" src docs tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- score por agente passa a ser reprodutível e persistente;
- a trilha P2 fica um passo mais concreta sem tocar no núcleo aprovado;
- a validação demonstra que o fluxo principal segue íntegro.

### Ajuste adicional nesta continuação
- `MetricsAggregator` passou a contar rounds únicos, preencher `avg_rounds_per_task` e expor `gates_blocked` do `progress.json`.
- `ReleaseReadinessEngine` e `GATE_8` passaram a bloquear drift `critical` além de `high`.
- a métrica de custo por agente e o contrato de `delivery-metrics.json` ficaram mais coerentes com o estado real.

### Validação executada
- Completa: `pytest -q` -> `207/207`.
- Demo: `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`.
