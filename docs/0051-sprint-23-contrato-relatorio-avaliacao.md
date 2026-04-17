# 0051 - Sprint 23 - Contrato do relatório de avaliação

## Objetivo

Fechar o contrato documental do `evaluation-report.json` para refletir o formato real já produzido pelo evaluator, sem perder compatibilidade com a leitura operacional atual.

## Estado de partida

Após a Sprint 22:
- runtime opt-in já existe e é observável
- adapters externos já são visíveis
- o evaluator já reconhece evidência estruturada parcial
- o relatório de avaliação já preserva resumo estruturado, mas o catálogo de artefatos ainda estava mais estreito que o payload real

O gap agora é puramente de contrato e documentação.

## Item da sprint

### Item único - alinhar `evaluation-report.json` ao payload real

Atualizar o contrato canônico do relatório de avaliação para refletir os campos realmente persistidos.

Resultado esperado:
- `evaluation-report.json` formaliza `sprint_id`, `spec_ref`, `result`, `criterion_results`, `criterios`, `status`, `evidencias`, `falhas`, `evidence_provided`, `evidence_missing`, `structured_evidence_count`, `structured_evidence_summary`, `next_action`, `round` e `timestamp`
- a leitura legível continua compatível com o fluxo atual
- o contrato fica auditável sem depender de interpretação do código

Arquivos-alvo:
- `src/cvg_harness/contracts/artifact_contracts.py`
- `src/cvg_harness/evaluator/evaluator.py`
- `tests/test_evaluator.py`
- documentação de apoio

## Critérios de saída

- o contrato do artefato corresponde ao payload efetivamente produzido
- o relatório continua validando e recarregando corretamente
- a trilha documental permanece honesta sobre o formato canônico

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
```

## Fechamento

Entrega concluída com o contrato do relatório de avaliação alinhado ao payload real:
- o catálogo de artefatos passou a exigir os campos canônicos do `evaluation-report.json`
- os testes de persistência e validação continuam verdes

Validação executada nesta rodada:
- `pytest -q` → `230 passed`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0052-sprint-24-sidecars-operacionais-canonicos.md`
