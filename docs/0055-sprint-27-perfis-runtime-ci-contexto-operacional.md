# 0055 - Sprint 27 - Perfis runtime/CI com contexto operacional

## Objetivo

Consolidar o perfil de runtime de CI para que ele receba contexto operacional derivado da própria ingestão de `ci_result`, mantendo o harness como orquestrador e reduzindo placeholders soltos na execução do hook.

## Estado de partida

Após a Sprint 26:
- `runtime-profiles` já lista perfis conhecidos
- `ci-readonly` já existe como perfil de runtime
- `ci-result.json` já é sidecar canônico
- o operador já aceita `--ci-result-file` e `--ci-result-url`

O gap restante era de contexto de execução:
- o hook de CI ainda não recebia, de forma consistente, os campos derivados da ingestão
- isso enfraquecia a leitura do comando executado em modo simulado ou real

## Item do sprint

### Item único - contexto operacional para hook de CI

Derivar contexto do `ci_result` para a execução do hook, de modo que o comando reflita a fonte informada sem perder o contrato canônico do sidecar.

Resultado esperado:
- o hook de CI recebe `ci_api` derivado de `ci_result_url` ou `ci_result_file` quando apropriado
- `runtime_hooks.results[0].command` fica coerente com a fonte informada
- `ci-result.json` continua sendo o sidecar canônico
- a UX de runtime profiles continua preservada

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `tests/test_operator_cli.py`
- documentação de apoio

## Critérios de saída

- o comando executado para `ci_result` reflete o contexto operacional fornecido
- o sidecar de CI permanece válido e canônico
- o operador continua simples e legível
- a suíte permanece verde

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
```

## Fechamento

Entrega concluída com contexto operacional de CI derivado no runtime.

Validação executada nesta rodada:
- `pytest -q` → `242 passed`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0056-sprint-28-perfis-reais-de-hooks-adapters-de-ci.md`
