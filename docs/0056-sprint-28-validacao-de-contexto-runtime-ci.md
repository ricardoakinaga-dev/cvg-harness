# 0056 - Sprint 28 - Validação de contexto em perfis runtime/CI

## Objetivo

Endurecer o uso operacional dos perfis de runtime/CI, validando compatibilidade entre perfil e evento e explicitando o contexto mínimo esperado antes de execução real.

## Estado de partida

Após a Sprint 27:
- `runtime-profiles` já listava perfis conhecidos
- `runtime --profile ...` já selecionava perfis operacionais
- `runtime-hooks.json` já preservava `profile`
- `ci-result.json` já existia como sidecar canônico para runtime de CI

O gap restante era de segurança operacional:
- perfis ainda podiam aceitar eventos incompatíveis sem falha explícita
- o sidecar de runtime ainda não tornava claras as lacunas de contexto
- execução real ainda não barrava contextos obviamente insuficientes

## Item do sprint

### Item único - validação explícita de contexto e compatibilidade

Materializar no operador uma validação mínima entre `profile`, `event` e `context`, preservando o modo simulado e bloqueando execução real sem contexto compatível.

Resultado esperado:
- perfil incompatível com evento falha explicitamente
- `runtime-hooks.json` passa a incluir `context_hints`, `missing_context_hints` e `available_context_keys`
- `inspect` expõe essas lacunas no resumo causal
- execução real (`--real`) falha quando não houver contexto mínimo compatível
- o help e a UX continuam simples

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `src/cvg_harness/auto_runtime/runtime_automation.py`
- `tests/test_operator_cli.py`
- `docs/0007-contratos-dos-artefatos.md`

## Critérios de saída

- perfis não suportam silenciosamente eventos fora do seu escopo
- sidecar de runtime preserva lacunas e chaves disponíveis
- modo simulado continua tolerante e visível
- modo real deixa de aceitar contexto insuficiente
- a suíte permanece verde

## Fechamento

Entrega concluída com validação explícita de contexto em runtime/CI:
- `OperatorService` rejeita combinações inválidas de `profile` + `event`
- `runtime-hooks.json` passou a registrar `context_hints`, `missing_context_hints` e `available_context_keys`
- `inspect` expõe as lacunas no resumo causal
- execução real de runtime bloqueia quando falta contexto mínimo compatível
- o contrato documental do sidecar de runtime foi ampliado para refletir esse payload real

Validação executada nesta rodada:
- `pytest -q tests/test_operator_cli.py tests/test_runtime.py` → `44 passed`
- `pytest -q` → `247 passed`

Encadeamento:
- próximo ciclo incremental abriu atalhos de contexto por provider no modo operador, preservando os perfis reais e reduzindo atrito para `github-actions` e `gitlab-ci`
