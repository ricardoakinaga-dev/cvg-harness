# 0063 - Sprint 35 - Fallback explícito por capability

## Objetivo

Transformar a seleção por capability em guidance operacional mais útil, registrando no plano externo não só o adapter escolhido, mas também as alternativas ordenadas para fallback humano.

## Estado de partida

Após a Sprint 34:
- `dispatch --capability ...` já escolhia um adapter automaticamente
- policies por capability já influenciavam a escolha (`review` preferindo `manual-review`)
- o gap restante era de transparência operacional: o operador ainda via a escolha final, mas não a fila explícita de alternativas para fallback

## Item único

### Alternativas ordenadas no plano de dispatch

Persistir no `external-dispatch-plan.json` as alternativas ordenadas ao adapter escolhido quando houver seleção por capability.

Resultado esperado:
- o plano externo registra `alternative_adapters`
- cada alternativa preserva `name`, `provider`, `suitability_score`, `selection_reason` e `missing_required_context`
- `dispatch` mostra essas alternativas na saída humana
- `inspect` passa a carregar essas alternativas no bloco causal de execução externa
- o operador passa a ter fallback explícito sem automação cega

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `tests/test_operator_cli.py`
- `docs/0007-contratos-dos-artefatos.md`
- `README.md`

## Critérios de saída

- `external-dispatch-plan.json` persiste alternativas ordenadas
- `dispatch --capability ...` mostra alternatives na saída humana
- `review` continua priorizando `manual-review`, mas expõe fallback explícito
- a suíte permanece verde

## Fechamento

Entrega concluída com fallback explícito por capability:
- `external-dispatch-plan.json` agora persiste `alternative_adapters`
- o operador enxerga fallback ordenado no próprio `dispatch`
- o bloco causal de execução externa preserva a fila de alternativas
- o handoff externo ficou mais auditável sem virar execução automática

Validação executada nesta rodada:
- `pytest -q tests/test_operator_cli.py tests/test_runtime.py` → `67 passed`
- `pytest -q` → `267 passed`
- `python3 -m cvg_harness adapters --capability review` → `manual-review` com fallback explícito implícito na ordenação
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental pode transformar esse fallback ordenado em políticas configuráveis por projeto, mantendo o operador no controle final


## Continuidade
- próximo ciclo incremental consolidado em `docs/0064-sprint-36-politicas-configuraveis-por-projeto.md`
