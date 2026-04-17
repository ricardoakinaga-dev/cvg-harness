# 0052 - Sprint 24 - Sidecars operacionais canônicos

## Objetivo

Formalizar os sidecars operacionais mais recentes do operador como artefatos canônicos, mantendo a UX leve e a separação entre harness, executor externo e runtime.

## Estado de partida

Após a Sprint 23:
- o relatório de avaliação já tem contrato canônico alinhado ao payload real
- runtime opt-in já existe e é observável
- dispatch externo opt-in já existe e é observável
- ainda faltava fechar contratos explícitos para os sidecars operacionais que já eram persistidos pela UX

O gap agora é de contrato e rastreabilidade, não de engine.

## Item do sprint

### Item único - contratos canônicos para sidecars operacionais

Formalizar os artefatos operacionais persistidos pelo operador que ainda não tinham contrato explícito no catálogo.

Resultado esperado:
- `external-dispatch-result.json` passa a ter contrato canônico
- `runtime-hooks.json` passa a ter contrato canônico
- os testes verificam que os sidecars persistidos batem com o contrato, incluindo o manifest complementar de evidência externa
- a documentação deixa claro que esses artefatos são sidecars operacionais, não nova fonte de verdade

Arquivos-alvo:
- `src/cvg_harness/contracts/artifact_contracts.py`
- `tests/test_operator_cli.py`
- documentação de apoio

## Critérios de saída

- sidecars operacionais novos aparecem no catálogo de artefatos
- dispatch externo e runtime continuam funcionando como antes
- a leitura documental permanece honesta sobre o papel de cada sidecar

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
```

## Fechamento

Entrega concluída com os sidecars operacionais formalizados no catálogo:
- `external-dispatch-result.json` ganhou contrato explícito
- `runtime-hooks.json` ganhou contrato explícito
- `external-evidence-manifest.json` ficou validado como sidecar complementar de runtime
- os testes de operator/runtime validam os sidecars contra o contrato

Validação executada nesta rodada:
- `pytest -q` → `230 passed`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0053-sprint-25-ci-result-operacional-canonico.md`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0053-sprint-25-ci-result-operacional-canonico.md`
