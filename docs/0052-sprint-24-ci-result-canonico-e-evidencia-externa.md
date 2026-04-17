# 0052 - Sprint 24 - CI result canonico e evidência externa

## Objetivo

Transformar o evento `ci_result` em um artefato canônico próprio, com trilha explícita de evidência externa e visibilidade operacional no operador.

## Estado de partida

Após a Sprint 23:
- o runtime já gerava `external-evidence-manifest.json`
- a evidência externa já aparecia em `inspect`
- o event log já registrava `external_evidence_registered`
- as métricas já contavam o novo sinal externo

O gap restante era a integração de sinais de CI mais explícitos:
- o runtime tinha um hook `ci_result`
- mas ainda não existia um artefato canônico para CI
- nem uma distinção clara entre evidência externa genérica e resultado de CI

## Item do sprint

### Item único - CI result canonico

Persistir um manifesto canônico de CI, derivado do runtime opt-in, para representar resultado externo de pipeline/teste/validação.

Resultado esperado:
- artefato `ci-result.json` na run
- evento canônico `ci_result_registered`
- `inspect` exibindo o CI result quando existir
- métricas reconhecendo CI como sinal externo separado

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `src/cvg_harness/types.py`
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `tests/test_operator_cli.py`
- `tests/test_agents_extended.py`

## Critérios de saída

- `cvg runtime --event ci_result` deixa rastro canônico
- o operador vê o `ci_result` em `inspect`
- o event log registra `ci_result_registered`
- métricas contam o novo sinal sem regressão

## Fechamento

Entrega concluída com CI result canônico exposto na UX do operador:
- `ci-result.json` é persistido na run
- `ci_result_registered` entra na timeline, nas métricas e no resumo exibido por `inspect`
- o fluxo legado continua estável

Validação executada nesta rodada:
- `pytest -q` -> `232 passed`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0053-sprint-25-ingestao-real-de-ci-result.md`
