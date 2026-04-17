# 0049 - Sprint 21 - Relatório de avaliação canônico

## Objetivo

Formalizar o `evaluation-report.json` como artefato canônico do evaluator, alinhando o contrato documental ao formato já preservado pelo código e mantendo a leitura humana e a leitura estruturada ao mesmo tempo.

## Estado de partida

Após a Sprint 20:
- o operador já expõe adapters conhecidos
- o hand-off externo já existe como sidecar explícito
- o evaluator já reconhece evidência estruturada parcial
- o relatório de avaliação ainda carrega mais riqueza no código do que o contrato documental explicita

O gap agora é de contrato, não de arquitetura básica.

## Item da sprint

### Item único - contrato canônico para `evaluation-report.json`

Alinhar o artefato de avaliação ao formato efetivamente produzido pelo evaluator.

Resultado esperado:
- `evaluation-report.json` expõe um resumo estruturado das evidências reconhecidas
- o relatório mantém compatibilidade com a leitura atual por `result` e `criterion_results`
- a documentação deixa explícito que o relatório é canônico e que o resumo estruturado é parte do contrato

Arquivos-alvo:
- `src/cvg_harness/evaluator/evaluator.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `tests/test_evaluator.py`
- documentação de apoio

## Critérios de saída

- o relatório de avaliação preserva campos canônicos e campos de apoio estruturado
- o contrato do artefato reflete o formato real produzido pelo evaluator
- a leitura operacional do fluxo continua estável

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
```

## Fechamento

Entrega concluída com o contrato do relatório de avaliação alinhado ao formato real:
- `EvaluationReport` passa a preservar `criterios`, `status`, `evidencias` e `falhas` além dos campos já existentes
- `evaluation-report.json` fica validável contra o contrato canônico sem perder compatibilidade operacional

Validação executada nesta rodada:
- `pytest -q` → `225 passed`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`
