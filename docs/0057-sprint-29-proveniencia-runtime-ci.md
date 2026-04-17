# 0057 - Sprint 29 - Proveniência de runtime/CI nos sidecars

## Objetivo

Explicitar a proveniência operacional dos sidecars de runtime/CI, carregando `provider` nos artefatos canônicos e tornando essa origem visível no operador, sem alterar a engine nem o contrato de aprovação.

## Estado de partida

Após a Sprint 28:
- `runtime-hooks.json` já carregava contexto, lacunas e perfil
- `ci-result.json` já era sidecar canônico
- `inspect` já mostrava metadados de perfil para leitura humana
- `runtime-profiles` já listava provider e exemplos de comando

O gap restante era de rastreabilidade:
- os sidecars ainda não preservavam `provider` como campo explícito do payload
- a proveniência ficava mais legível na inspeção do que no artefato persistido

## Item do sprint

### Item único - provider explícito em sidecars de runtime/CI

Adicionar `provider` aos sidecars de runtime e CI e refletir essa informação no `inspect` do operador.

Resultado esperado:
- `runtime-hooks.json` passa a persistir `provider`
- `ci-result.json` passa a persistir `provider`
- `inspect` expõe a proveniência de runtime/CI com mais clareza
- os contratos dos sidecars ficam alinhados ao payload real

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `src/cvg_harness/cli/cli.py`
- `tests/test_operator_cli.py`
- documentação de apoio

## Critérios de saída

- o payload persistido carrega a proveniência do perfil usado
- a leitura humana fica mais transparente sem inflar a superfície da CLI
- os sidecars canônicos continuam estáveis
- a suíte permanece verde

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
```

## Fechamento

Entrega concluída com proveniência explícita em runtime/CI.

Validação executada nesta rodada:
- `pytest -q` → `247 passed in 1.68s`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0058-sprint-30-observabilidade-de-provider.md`
