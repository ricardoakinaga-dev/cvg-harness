# 0058 - Sprint 30 - Observabilidade de provider em métricas/dashboard

## Objetivo

Transformar `provider` em sinal operacional agregado, para que métricas e dashboard mostrem a origem dos eventos de runtime/CI além do payload persistido e da inspeção humana.

## Estado de partida

Após a Sprint 29:
- `runtime-hooks.json` e `ci-result.json` já carregam `provider`
- `inspect` já expõe `provider`, `profile` e metadados do runtime
- `runtime-profiles` já lista `provider` e exemplos de comando
- o event log já carrega `provider` nas metadatas dos eventos de runtime/CI

O gap restante era de observabilidade:
- `provider` ainda não aparecia agregado em `delivery-metrics.json`
- o dashboard ainda não mostrava a quebra dos eventos por provider

## Item do sprint

### Item único - provider agregado em métricas e dashboard

Agrupar eventos de runtime/CI por `provider` e tornar esse sinal visível nos artefatos de observabilidade.

Resultado esperado:
- `delivery-metrics.json` passa a carregar `runtime_provider_breakdown`
- `dashboard.json` passa a carregar `runtime_provider_breakdown`
- os eventos de runtime/CI continuam canônicos e opt-in
- o operador mantém leitura simples

Arquivos-alvo:
- `src/cvg_harness/metrics/metrics_catalog.py`
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `src/cvg_harness/dashboard/dashboards.py`
- `src/cvg_harness/operator/service.py`
- `tests/test_agents_extended.py`
- documentação de apoio

## Critérios de saída

- provider deixa de ser apenas metadado de inspeção e passa a sinal agregado
- métricas e dashboard compartilham a mesma semântica
- o contrato dos sidecars canônicos continua estável
- a suíte permanece verde

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
```

## Fechamento

Entrega concluída com `provider` agregado em métricas e dashboard.

Validação executada nesta rodada:
- `pytest -q` → `253 passed in 2.07s`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- o provider agregado em métricas e dashboard fica como base para a Sprint 31, com `dispatch` provider-aware consolidado em `docs/0060-sprint-31-contexto-provider-no-dispatch.md`
