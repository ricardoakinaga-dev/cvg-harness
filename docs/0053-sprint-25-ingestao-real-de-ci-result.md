# 0053 - Sprint 25 - Ingestao real de CI result

## Objetivo

Permitir que o operador registre um resultado de CI externo concreto por arquivo ou JSON inline, sem depender apenas do hook simulado do runtime, mantendo a separação entre harness e executor.

## Estado de partida

Após a Sprint 24:
- `ci-result.json` já existia como artefato canônico
- `ci_result_registered` já entrava na timeline e nas métricas
- `inspect` já mostrava o resultado de CI quando ele existia
- o runtime já suportava `ci_result` em modo opt-in

O gap restante era a ingestão real:
- o operador ainda precisava conseguir apontar para um resultado externo concreto
- o runtime ainda era mais gerador de contrato do que ingestor de payload externo

## Item do sprint

### Item único - ingestão externa de CI result

Aceitar o resultado de CI como entrada externa por arquivo ou JSON inline e persistir o mesmo contrato canônico na run.

Resultado esperado:
- `cvg runtime --event ci_result --ci-result-file ...`
- `cvg runtime --event ci_result --ci-result-json ...`
- `ci-result.json` refletindo o payload externo informado
- `inspect` mostrando o resultado externalizado

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `tests/test_operator_cli.py`

## Critérios de saída

- o operador pode registrar CI real via arquivo ou JSON inline
- o event log continua canônico
- métricas continuam estáveis
- a trilha não perde a separação entre harness e executor

## Fechamento

Entrega concluída com ingestão externa de CI result:
- o runtime aceita `--ci-result-file` e `--ci-result-json`
- o artefato `ci-result.json` reflete o payload externo
- `inspect` mostra o resultado de CI externo quando presente
- o fluxo legado continua estável

Validação executada nesta rodada:
- `pytest -q` -> `233 passed`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0054-sprint-26-fontes-reais-de-ci-por-url.md`
