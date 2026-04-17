# 0056 - Sprint 28 - Perfis reais de hooks/adapters de CI

## Objetivo

Tornar os perfis de runtime/CI mais legíveis para operação humana, expondo metadados de provider, exemplos de comando e contexto esperado no `inspect` e na CLI, sem alterar o contrato canônico dos sidecars já aprovados.

## Estado de partida

Após a Sprint 27:
- `runtime-profiles` já lista perfis conhecidos
- `ci-readonly`, `quality-gates`, `github-actions` e `gitlab-ci` já existem no catálogo de runtime
- o runtime de `ci_result` já recebe contexto derivado da ingestão
- o operador já expõe `ci-result.json` como sidecar canônico

O gap restante era de UX operacional:
- o `inspect` ainda mostrava o runtime como bloco bruto
- os metadados do perfil estavam disponíveis, mas não eram explicitados na inspeção humana

## Item do sprint

### Item único - leitura humana enriquecida dos perfis de CI

Expor metadados do perfil de runtime no resumo causal e na saída humana do operador.

Resultado esperado:
- `inspect` mostra provider e exemplos de comando do perfil de runtime
- `cmd runtime` imprime provider e exemplos quando disponíveis
- `runtime-profiles` continua listando os perfis conhecidos
- o contrato do sidecar de CI não muda

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `tests/test_operator_cli.py`
- documentação de apoio

## Critérios de saída

- o operador identifica rapidamente qual perfil está ativo
- os perfis de CI deixam de depender só de leitura do código
- o fluxo principal e os sidecars canônicos continuam estáveis
- a suíte permanece verde

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
```

## Fechamento

Entrega concluída com leitura humana enriquecida dos perfis de CI.

Validação executada nesta rodada:
- `pytest -q` → `242 passed in 5.54s`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0057-sprint-29-proveniencia-runtime-ci.md`
