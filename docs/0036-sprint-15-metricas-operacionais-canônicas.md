# 0036. Sprint 15 - Métricas operacionais canônicas

## Objetivo
Fechar a frente de `analytics/observability P2` mais próxima do estado real do repositório: tornar o `MetricsAggregator` capaz de gerar `delivery-metrics.json` canônico a partir de eventos e progresso reais, sem reabrir o núcleo aprovado do fluxo.

## Estado de partida
- O projeto segue aprovado e com o fluxo fim a fim estável.
- O contrato de `delivery-metrics.json` já existe em `docs/0007-contratos-dos-artefatos.md` e `src/cvg_harness/contracts/artifact_contracts.py`.
- O agregador já consolida métricas internas, mas ainda não expunha um caminho canônico simples para gerar o artefato de entrega a partir do `event-log.jsonl`.
- A interface do REPL também não materializava métricas sob demanda a partir do workspace quando o arquivo ainda não existia.

## Itens do sprint (execução limitada a este bloco)

### 1) Exportar delivery-metrics canônico do agregador
**Status:** `done`

Arquivos alvo:
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `tests/test_agents_extended.py`
- `src/cvg_harness/metrics/metrics_catalog.py`

Mudanças esperadas:
- converter métricas agregadas em `DeliveryMetrics` canônico;
- salvar `delivery-metrics.json` a partir de eventos reais e progress quando solicitado;
- preservar compatibilidade com o contrato já documentado.

Resultado desta rodada:
- `MetricsAggregator` passou a exportar `delivery-metrics.json` canônico;
- o contrato passou a ser validado por teste com eventos reais;
- o JSON gerado pode ser consumido por ferramentas e pelo REPL.

Critérios de saída:
- `delivery-metrics.json` nasce com os campos canônicos esperados;
- a cobertura prova o export a partir de eventos reais.

### 2) Tornar métricas acessíveis sob demanda no REPL
**Status:** `done`

Arquivos alvo:
- `src/cvg_harness/repl.py`
- `tests/test_agents_extended.py`

Mudanças esperadas:
- gerar métricas no workspace quando `delivery-metrics.json` ainda não existir;
- usar `progress.json` quando disponível para contexto;
- manter a saída legível para operação local.

Resultado desta rodada:
- o comando `metrics` do REPL passa a materializar métricas quando há `event-log.jsonl`;
- a leitura operacional fica mais próxima do estado real do workspace.

Critérios de saída:
- o operador consegue obter métricas sem preparar o artefato manualmente;
- o comportamento permanece limitado ao workspace atual.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
pytest -q tests/test_agents_extended.py tests/test_agents.py tests/test_pr03_flow_orchestrator.py
rg -n "delivery-metrics|MetricsAggregator|metrics" src docs tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- `delivery-metrics.json` passa a ter um caminho canônico de geração;
- o REPL consegue expor métricas operacionais sem trabalho manual extra;
- a mudança permanece incremental e não toca release, gates ou planning já estabilizados.

### Validação executada
- Completa: `pytest -q` -> `189/189`.
- Demo: `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`.

## Encadeamento
- Sprint anterior: `docs/0035-sprint-14-contratos-criticos-no-spec-builder.md`.
- Próximo ciclo documentado em: `docs/0038-sprint-16-endurecimento-guardian-drift.md`.
