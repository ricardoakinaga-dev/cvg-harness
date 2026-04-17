# 0057 - Sprint 29 - Contexto executável por provider

## Objetivo

Reduzir a abstração dos perfis de runtime/CI, fazendo com que os providers conhecidos recebam contexto operacional concreto e resolvido a partir do `ci_result`, sem perder a neutralidade do harness.

## Estado de partida

Após a Sprint 28:
- `runtime-profiles` já expunha `provider`, `command_examples` e `context_hints`
- os perfis `github-actions` e `gitlab-ci` já existiam
- o operador já preservava o comportamento opt-in
- o runtime já carregava `ci_result` por arquivo, JSON inline e URL

O gap restante era a concretude do contexto:
- os perfis ainda eram mais descritivos do que executáveis
- faltava um contrato explícito de contexto requerido por provider
- faltava uma resolução automática de contexto para o comando refletir a origem real do CI

## Item do sprint

### Item único - contexto resolvido por provider

Adicionar contrato de contexto e resolução operacional para perfis de runtime/CI, mantendo o harness como orquestrador.

Resultado esperado:
- `runtime-profiles` exibindo `required_context` e `example_contexts`
- `github-actions` resolvendo `repository` e `ci_run_id` a partir do `ci_result`
- `gitlab-ci` preservando `ci_api` e `ci_result_url` como contexto canônico
- `runtime-hooks.json` registrando contexto bruto e contexto resolvido
- `ci-result.json` continuando canônico e rastreável

Arquivos-alvo:
- `src/cvg_harness/auto_runtime/runtime_automation.py`
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `tests/test_runtime.py`
- `tests/test_operator_cli.py`

## Critérios de saída

- os perfis deixam de ser apenas catálogo e passam a carregar contrato de contexto
- o runtime executa comandos mais concretos para providers conhecidos
- a ingestão de CI continua opt-in e sem acoplamento rígido
- a suíte permanece verde

## Fechamento

Entrega concluída com contexto executável por provider:
- `runtime-profiles` agora mostra `required_context` e `example_contexts`
- `github-actions` resolve automaticamente `repository` e `ci_run_id` quando recebe `ci_result`
- `gitlab-ci` mantém o caminho canônico de `ci_api` e `ci_result_url`
- `runtime-hooks.json` passa a registrar `raw_context` e `resolved_context`
- o fallback legado de `ci_api` continua funcionando para ingestão por arquivo e URL

Validação executada nesta rodada:
- `pytest -q` -> `245 passed`

Encadeamento:
- próximo ciclo incremental deve expandir os contracts para mais providers reais ou consolidar a UX de operador para esses novos campos resolvidos
