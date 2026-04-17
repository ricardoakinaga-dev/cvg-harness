# 0062 - Sprint 34 - Políticas por capability no handoff

## Objetivo

Deixar a seleção por capability menos neutra e mais alinhada à intenção operacional, sem esconder a escolha real do adapter nem acoplar o harness a um fornecedor específico.

## Estado de partida

Após a Sprint 33:
- `cvg adapters --capability ...` já ranqueava adapters por capability e contexto
- `cvg dispatch --capability ...` já auto-selecionava o melhor adapter disponível
- o gap restante estava na política: toda capability era tratada quase igual, sem preferência explícita por tipo de handoff

## Item único

### Policies explícitas por capability

Adicionar políticas mínimas por capability no operador, tornando a preferência observável no score e no reason.

Resultado esperado:
- `review` prefere `manual-review` por padrão
- `ci` continua priorizando provider compatível com o contexto observado
- `selection_reason` passa a refletir policy além de capability/provider/contexto
- o operador entende por que um adapter humano ou automático foi priorizado

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `tests/test_operator_cli.py`
- `docs/0045-contratos-para-executores-externos.md`
- `README.md`

## Critérios de saída

- `adapters --capability review` ranqueia `manual-review` em primeiro lugar
- `dispatch --capability review` seleciona `manual-review`
- a escolha continua explícita via `selection_reason`
- a suíte permanece verde

## Fechamento

Entrega concluída com políticas mínimas por capability:
- `review` agora prefere `manual-review` por policy explícita
- `ci` continua sendo orientado por capability + provider/contexto
- `selection_reason` e `suitability_score` ficaram mais informativos para auditoria

Validação executada nesta rodada:
- `pytest -q tests/test_operator_cli.py tests/test_runtime.py` → `67 passed`
- `pytest -q` → `267 passed`
- `python3 -m cvg_harness adapters --capability review` → `manual-review` em primeiro lugar
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental pode consolidar políticas mais ricas por capability, por exemplo fallback ordenado `ci -> review -> evidence`, ou preferências configuráveis por projeto sem quebrar o modo operador canônico
