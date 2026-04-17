# 0051 - Sprint 23 - Evidencia externa canonica

## Objetivo

Transformar a saida dos hooks de runtime em evidencia externa canonica, com manifesto proprio, evento de timeline e visibilidade operacional na UX do operador.

## Estado de partida

Após a Sprint 22:
- o runtime opt-in ja podia ser executado em modo simulated ou real
- `runtime-hooks.json` ja era persistido na run
- `runtime_hooks_executed` ja entrava na timeline e nas metricas
- o `inspect` ja mostrava o runtime para o operador

O gap restante era a formalizacao da saida externa:
- hooks geravam resultado, mas ainda não havia um manifesto canônico de evidência externa
- a trilha operacional ainda não distinguia claramente runtime executado de evidência externa registrada

## Item do sprint

### Item unico - external evidence manifesto

Persistir um manifesto canônico de evidência externa derivado dos resultados do runtime e expor esse sinal no operador, em `inspect`, timeline e métricas.

Resultado esperado:
- artefato `external-evidence-manifest.json` na run
- evento canônico `external_evidence_registered`
- `inspect` exibindo evidência externa quando existir
- métricas reconhecendo a evidência externa como sinal adicional

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `src/cvg_harness/types.py`
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `tests/test_operator_cli.py`
- `tests/test_agents_extended.py`

## Critérios de saída

- runtime gera um manifesto externo rastreavel
- o operador vê a evidência externa em `inspect`
- o event log registra a evidência externa separadamente do simples runtime executado
- métricas continuam estáveis e passam a contar o novo sinal

## Fechamento

Entrega concluída com evidencia externa canonica exposta na UX do operador:
- `external-evidence-manifest.json` é persistido na run
- `external_evidence_registered` entra na timeline e nas métricas
- `inspect` mostra a evidência externa quando ela existe
- o fluxo legado continua estável

Validação executada nesta rodada:
- `pytest -q` -> `230 passed`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0052-sprint-24-ci-result-canonico-e-evidencia-externa.md`
