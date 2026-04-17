# 0060 - Sprint 32 - Proveniência de runtime no resultado externo

## Objetivo

Levar a proveniência operacional derivada do runtime para o `external-dispatch-result.json`, para que o resultado formal do dispatch externo espelhe o contexto já resolvido no plano.

## Nota histórica

Este documento representa a etapa intermediária entre o dispatch provider-aware e o fechamento causal consolidado em `docs/0061-sprint-33-contexto-causal-no-dispatch-concluido.md`.
Atualização posterior: a leitura humana do dispatch concluído foi refinada em `docs/0062-sprint-34-inspecao-humana-do-dispatch-concluido.md`.

## Estado de partida

Após a Sprint 31:
- `external-dispatch-plan.json` já carrega `runtime_profile` e `runtime_provider`
- `cvg dispatch` já mostra o provider do adapter e o runtime provider derivado
- `inspect` já expõe o mesmo contexto causal
- o dispatch externo continua opt-in e controlado

O gap restante era a simetria do resultado:
- `external-dispatch-result.json` ainda era mais pobre que o plano em proveniência operacional
- a leitura do dispatch concluído mostrava a execução, mas não o contexto de runtime que a antecedeu

## Item do sprint

### Item único - runtime provider explícito no resultado externo

Persistir `runtime_profile` e `runtime_provider` no resultado formal do dispatch externo, preservando também `context_sources` e a separação entre planejamento e execução.

Resultado esperado:
- `external-dispatch-result.json` carrega `runtime_profile` e `runtime_provider`
- `inspect` expõe a mesma proveniência no bloco de dispatch concluído
- a validação do contrato reconhece o payload enriquecido
- o contrato opt-in do executor externo continua estável

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `tests/test_operator_cli.py`
- documentação de apoio

## Critérios de saída

- o resultado externo deixa explícita a proveniência do runtime que o precedeu
- plano e resultado compartilham o mesmo contexto causal
- o provider do adapter continua separado da proveniência do runtime
- a suíte permanece verde

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
```

## Fechamento

Entrega concluída com proveniência explícita no resultado externo.

Validação executada nesta rodada:
- `pytest -q` -> `261 passed`
- `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0061-sprint-33-contexto-causal-no-dispatch-concluido.md`
