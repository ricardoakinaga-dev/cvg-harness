# 0061 - Sprint 33 - Seleção de adapter por capability

## Objetivo

Permitir que o operador escolha o adapter externo pelo que precisa fazer, e não só pelo nome do adapter, mantendo a escolha final explícita e auditável.

## Estado de partida

Após a Sprint 32:
- o registry default já tinha adapters provider-aware reais
- `cvg adapters` já expunha provider, contexto mínimo e exemplos de comando
- `dispatch` já aceitava contexto provider-aware
- o gap restante era de UX do operador: ainda era preciso saber o nome do adapter certo mesmo quando a necessidade era só `ci`, `review` ou `evidence`

## Item único

### Capability-aware ranking e auto-seleção de adapter

Adicionar ranqueamento de adapters por capability no operador e permitir auto-seleção em `dispatch` quando o operador informar a capability desejada.

Resultado esperado:
- `cvg adapters --capability ci` ranqueia adapters compatíveis para o contexto atual da run
- `cvg dispatch --capability ci` escolhe o melhor adapter disponível sem esconder qual foi escolhido
- o plano externo registra `capability`, `selection_reason` e `suitability_score`
- a seleção continua explícita, observável e opt-in
- o harness continua sendo o orquestrador, não o executor automático

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `tests/test_operator_cli.py`
- `README.md`
- `docs/0045-contratos-para-executores-externos.md`

## Critérios de saída

- `adapters` ranqueia por capability e contexto atual
- `dispatch` aceita `--capability` quando `--executor` não for informado
- a escolha do adapter fica visível na saída humana e no sidecar de dispatch
- a suíte permanece verde

## Fechamento

Entrega concluída com seleção de adapter por capability:
- `cvg adapters` passou a ranquear adapters por capability no contexto atual da run
- `cvg dispatch --capability ...` auto-seleciona o adapter mais adequado
- o plano externo agora registra `capability`, `selection_reason` e `suitability_score`
- a escolha do adapter continua explícita e auditável

Validação executada nesta rodada:
- `pytest -q tests/test_operator_cli.py tests/test_runtime.py` → `64 passed`
- `pytest -q` → `267 passed`
- `python3 -m cvg_harness dispatch --help` → `--capability` exposto
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental pode enriquecer políticas por capability no handoff externo, por exemplo preferências por `ci`, `review`, `evidence`, sem acoplamento cego do harness a fornecedores específicos
