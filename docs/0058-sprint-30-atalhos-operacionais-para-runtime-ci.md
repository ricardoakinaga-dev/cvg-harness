# 0058 - Sprint 30 - Atalhos operacionais para runtime/CI

## Objetivo

Reduzir o atrito do operador no uso de perfis reais de runtime/CI, aceitando contexto explícito por flags da CLI sem quebrar o contrato genérico baseado em `context-json`.

## Estado de partida

Após as Sprints 28 e 29:
- `runtime-profiles` já expunha `provider`, `required_context`, `example_contexts` e `command_examples`
- `OperatorService` já resolvia contexto por provider
- `runtime-hooks.json` e `ci-result.json` já persistiam `provider`, `raw_context` e `resolved_context`
- o gap restante era de UX do operador: ainda era preciso montar JSON manual para campos simples como `repository`, `ci_run_id` e `ci_api`

## Item único

### Atalhos explícitos de contexto na CLI de runtime

Adicionar flags operacionais de contexto no comando `cvg runtime`, preservando o caminho genérico por JSON.

Resultado esperado:
- `cvg runtime` aceita `--repository`, `--ci-run-id`, `--ci-api`, `--ci-url` e `--ci-status`
- esses campos são mesclados ao `context-json` sem quebrar compatibilidade
- a saída humana deixa de repetir linhas redundantes
- o operador enxerga `available_context_keys` na saída de runtime
- README e contrato vivo ficam alinhados ao fluxo real

Arquivos-alvo:
- `src/cvg_harness/cli/cli.py`
- `tests/test_operator_cli.py`
- `README.md`
- `docs/0007-contratos-dos-artefatos.md`

## Critérios de saída

- perfis reais podem ser usados sem JSON manual para os campos mais comuns
- `context-json` continua funcionando como fallback genérico
- a saída humana de `cvg runtime` fica mais clara
- a suíte permanece verde

## Fechamento

Entrega concluída com atalhos operacionais para runtime/CI:
- `cvg runtime` agora aceita contexto explícito por flags para providers reais
- a CLI mescla flags operacionais com `context-json`
- a saída humana passou a mostrar `available_context_keys` e removeu duplicidade de campos
- README e contrato documental foram alinhados ao payload real de runtime/CI

Validação executada nesta rodada:
- `pytest -q tests/test_operator_cli.py tests/test_runtime.py` → `52 passed`
- `pytest -q` → `257 passed`
- `python3 -m cvg_harness --help` → modo operador preservado

Encadeamento:
- próximo ciclo incremental aberto em `docs/0060-sprint-31-contexto-provider-no-dispatch.md`
