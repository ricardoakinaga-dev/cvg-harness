# 0050 - Sprint 22 - Runtime opt-in e evidência operacional

## Objetivo

Transformar o runtime já existente em uma superfície operacional opcional do operador, capaz de executar hooks simulados ou reais, registrar evidência e entrar na trilha canônica do harness.

## Estado de partida

Após a Sprint 21:
- o dispatch externo opt-in já era observável
- falhas externas já apareciam na timeline do operador
- métricas já contavam sinais externos de execução
- o evaluator já mantinha compatibilidade com contratos legados e estruturados

O gap restante era a camada de runtime:
- os hooks existiam como contrato
- mas ainda não estavam expostos como comando do operador
- e ainda não produziam artefato canônico na run

## Item do sprint

### Item único — runtime opt-in com evidência operacional

Expor a execução de hooks de runtime no modo operador, com simulação por padrão e opt-in explícito para execução real.

Resultado esperado:
- comando operacional para executar hooks de runtime
- persistência de `runtime-hooks.json` na run
- evento canônico de execução de runtime no event log
- `inspect` mostrando o artefato de runtime quando existir, inclusive na saída humana da CLI

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/types.py`
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `tests/test_operator_cli.py`
- `tests/test_agents_extended.py`

## Critérios de saída

- runtime pode ser executado em modo simulated ou real
- o operador vê o resultado em `inspect`
- a trilha documental continua honesta sobre o caráter opt-in
- métricas passam a contar runtime como sinal externo adicional

## Fechamento

Entrega concluída com runtime opt-in exposto na UX do operador:
- `cvg runtime` executa hooks em simulated por padrão
- `runtime-hooks.json` é persistido na run
- `runtime_hooks_executed` entra na timeline, nas métricas e no resumo exibido por `inspect`
- o fluxo legado continua estável

Validação executada nesta rodada:
- `pytest -q` → `230 passed`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0051-sprint-23-evidencia-externa-canonica.md`
