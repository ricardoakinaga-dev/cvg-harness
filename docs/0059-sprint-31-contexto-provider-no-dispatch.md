# 0059 - Sprint 31 - Contexto de provider no dispatch externo

## Objetivo

Tornar explícito no hand-off de `dispatch` o `runtime_provider` derivado dos hooks reais, preservando a proveniência operacional no plano de execução externa e na leitura humana, sem alterar a natureza opt-in do executor externo.

## Nota histórica

Este documento registra a etapa intermediária da trilha provider-aware. O fechamento operacional da leitura de dispatch concluído foi consolidado em `docs/0061-sprint-33-contexto-causal-no-dispatch-concluido.md` e a inspeção humana legível foi refinada em `docs/0062-sprint-34-inspecao-humana-do-dispatch-concluido.md`.

## Estado de partida

Após a Sprint 30:
- `runtime-hooks.json` e `ci-result.json` já carregam `provider`
- `delivery-metrics.json` e `dashboard.json` já agregam `runtime_provider_breakdown`
- `cvg runtime` e `inspect` já expõem `provider` e `profile`
- o `dispatch` já carrega contexto resolvido e `context_sources`

O gap restante era de leitura e rastreabilidade:
- o plano de dispatch ainda não tornava o `runtime_provider` tão explícito quanto o restante do contrato de runtime/CI
- a superfície humana de `dispatch` ainda mostrava mais o provider do adapter externo do que a proveniência operacional derivada do runtime

## Item do sprint

### Item único - runtime provider explícito no hand-off de dispatch

Preservar `runtime_profile` e `runtime_provider` no plano de dispatch e tornar esse contexto visível em `inspect` e na CLI de `dispatch`.

Resultado esperado:
- `external-dispatch-plan.json` carrega `runtime_profile` e `runtime_provider` quando hooks reais existem
- `cvg dispatch` mostra o provider do adapter e o runtime provider derivado
- `inspect` expõe o mesmo contexto na leitura causal
- o contrato opt-in do executor externo continua estável

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `tests/test_operator_cli.py`
- documentação de apoio

## Critérios de saída

- o hand-off externo passa a carregar a proveniência do runtime de forma explícita
- o provider do adapter e o runtime provider não se confundem na leitura humana
- `inspect` e `dispatch` mostram o mesmo contexto derivado
- a suíte permanece verde

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
```

## Fechamento

Entrega concluída como etapa intermediária histórica da trilha provider-aware em dispatch.

Resumo:
- `external-dispatch-plan.json` passou a carregar `runtime_profile` e `runtime_provider`
- `dispatch` passou a mostrar o provider do adapter e o runtime provider derivado
- `inspect` passou a expor o mesmo contexto na leitura causal
- o contrato opt-in do executor externo permaneceu estável

Validação executada nesta etapa:
- `pytest -q` → `261 passed`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0060-sprint-32-proveniencia-no-resultado-externo.md`
