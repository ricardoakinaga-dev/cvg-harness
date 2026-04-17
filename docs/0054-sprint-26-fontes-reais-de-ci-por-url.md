# 0054 - Sprint 26 - Fontes reais de CI por URL

## Objetivo

Permitir que a ingestão de `ci_result` consuma uma fonte externa concreta via URL JSON, mantendo o harness como orquestrador e evitando acoplamento a um provedor específico.

## Estado de partida

Após a Sprint 25:
- o operador já podia registrar `ci_result` por arquivo ou JSON inline
- `ci-result.json` já era persistido como artefato canônico
- `ci_result_registered` já entrava na timeline e nas métricas
- o CLI já expunha perfis de runtime conhecidos

O gap restante era a fonte externa real:
- a ingestão ainda dependia de entrada local ou inline
- não havia caminho simples para consumir um payload remoto JSON

## Item do sprint

### Item único - ingestão de CI via URL

Aceitar um JSON remoto como fonte externa de `ci_result`, preservando o contrato canônico e a rastreabilidade operacional.

Resultado esperado:
- `cvg runtime --event ci_result --ci-result-url ...`
- `ci-result.json` refletindo o payload remoto
- `inspect` exibindo o CI result remoto quando presente
- `runtime-profiles` preservando a descoberta de perfis conhecidos

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `tests/test_operator_cli.py`
- `tests/test_runtime.py`

## Critérios de saída

- o operador pode apontar para um JSON remoto como CI result
- o event log continua canônico
- métricas continuam estáveis
- os perfis conhecidos de runtime continuam visíveis

## Fechamento

Entrega concluída com ingestão de CI via URL:
- o runtime aceita `--ci-result-url`
- o artefato `ci-result.json` reflete o payload remoto informado
- `inspect` mostra o resultado de CI remoto quando presente
- a UX de runtime profiles continua disponível

Validação executada nesta rodada:
- `pytest -q` -> `238 passed`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0055-sprint-27-perfis-runtime-ci-contexto-operacional.md`
