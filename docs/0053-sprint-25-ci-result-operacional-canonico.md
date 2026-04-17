# 0053 - Sprint 25 - CI result operacional canônico

## Objetivo

Formalizar o resultado de CI derivado de runtime opt-in como sidecar operacional canônico, com visibilidade consistente em `inspect`, timeline e métricas.

## Estado de partida

Após a Sprint 24:
- `runtime-hooks.json` e `external-evidence-manifest.json` já eram sidecars operacionais canônicos
- o operador já conseguia executar hooks de runtime em modo `simulated` ou `real`
- a trilha de runtime já diferenciava `runtime_hooks_executed` de `external_evidence_registered`
- o código já carregava `ci-result.json` e `ci_result_registered`, mas esse avanço ainda não estava formalizado na trilha documental

O gap agora não era mais de engine. O gap era de canonicidade documental e rastreabilidade explícita desse sidecar de CI.

## Item do sprint

### Item único - sidecar canônico para resultado de CI

Consolidar `ci-result.json` como artefato operacional canônico derivado de runtime, com contrato explícito, inspeção humana e contagem nas métricas.

Resultado esperado:
- `ci-result.json` persistido quando `runtime` roda no evento `ci_result`
- evento `ci_result_registered` no `event-log.jsonl`
- `inspect` expondo resumo de CI no payload e na saída humana
- métricas reconhecendo `ci_result` como breakdown operacional distinto

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `tests/test_operator_cli.py`
- `tests/test_agents_extended.py`
- documentação de apoio

## Critérios de saída

- `ci-result.json` tem contrato explícito e validável
- o operador vê o resultado de CI em `inspect`
- timeline separa runtime executado de resultado de CI registrado
- métricas reconhecem `ci_result` como sinal operacional adicional
- a documentação continua honesta sobre o caráter opt-in e sidecar desse artefato

## Fechamento

Entrega concluída com o sidecar operacional de CI formalizado no produto:
- `ci-result.json` é persistido quando o runtime opera no evento `ci_result`
- `ci_result_registered` entra na timeline do operador
- `inspect` expõe o resumo de CI no payload causal
- `external_execution_breakdown` passa a incluir `ci_result`

Validação executada nesta rodada:
- `pytest -q` → `238 passed in 3.00s`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0055-sprint-27-perfis-runtime-ci-opt-in.md`
