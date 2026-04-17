# 0055 - Sprint 27 - Perfis de runtime/CI opt-in

## Objetivo

Adicionar uma camada leve de perfis conhecidos para runtime/CI no modo operador, reduzindo atrito de uso sem alterar a engine interna do harness.

## Estado de partida

Após a Sprint 25:
- `runtime` já existia como comando opt-in do operador
- `ci-result.json` já era sidecar operacional canônico
- `runtime-hooks.json`, `external-evidence-manifest.json` e `ci-result.json` já apareciam na trilha operacional
- ainda faltava uma forma simples de o operador selecionar um conjunto conhecido de hooks sem depender apenas do contrato bruto

O gap agora era de UX operacional, não de governança.

## Item do sprint

### Item único - perfis conhecidos de runtime/CI

Expor perfis conhecidos de runtime para o operador, preservando o comportamento opt-in e a separação entre harness, runtime e executor.

Resultado esperado:
- `runtime-profiles` lista os perfis conhecidos
- `runtime --profile ...` permite selecionar o perfil operacional desejado
- `runtime-hooks.json` persiste o perfil usado
- `inspect` mostra o perfil de runtime no resumo causal
- o help principal mantém o modo operador claro

Arquivos-alvo:
- `src/cvg_harness/auto_runtime/runtime_automation.py`
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `tests/test_runtime.py`
- `tests/test_operator_cli.py`

## Critérios de saída

- perfis conhecidos existem e são listáveis
- o operador consegue usar `--profile` sem quebrar o contrato atual de runtime
- o sidecar de runtime preserva o perfil utilizado
- a CLI continua operador-first
- a suíte continua verde

## Fechamento

Entrega concluída com perfis opt-in de runtime/CI expostos ao operador:
- `runtime-profiles` lista `default`, `ci-readonly` e `quality-gates`
- `runtime --profile ...` seleciona o perfil conhecido
- `runtime-hooks.json` preserva `profile`
- `inspect` expõe o perfil de runtime no resumo causal
- o `--help` principal agora mostra `runtime-profiles` junto do modo operador

Validação executada nesta rodada:
- `pytest -q` → `238 passed`
- `python3 -m cvg_harness --help` → modo operador inclui `runtime-profiles`
- `python3 -m cvg_harness runtime-profiles --json` → perfis conhecidos retornados

Encadeamento:
- próximo ciclo incremental aberto em `docs/0056-sprint-28-validacao-de-contexto-runtime-ci.md`
