# 0047 - Sprint 19 - Executor externo e evidência operacional

## Objetivo

Aprofundar a ponte entre o modo operador e a execução externa real sem quebrar a separação entre harness e executor.

## Estado de partida

Após a Sprint 18:
- `cvg run` e o loop operador já existem
- `inspect` já mostra causalidade relevante
- evidência estruturada já entra no sistema
- contratos para executores externos já existem

O gap agora não é arquitetura básica. O gap é integração controlada.

## Itens do sprint

### Item 1 — hand-off explícito para executor externo

Implementar uma forma controlada de o modo operador preparar um dispatch para um adapter externo conhecido.

Resultado esperado:
- gerar request formal de execução externa por sprint
- persistir o plano de dispatch na run
- não executar nada automaticamente por padrão

Arquivos-alvo prováveis:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/auto_runtime/external_executor.py`

### Item 2 — evaluator parcialmente orientado a evidência estruturada

Fazer o evaluator reconhecer ao menos `kind`, `ref` e `module` ao processar evidência estruturada, sem depender apenas do flatten textual.

Resultado esperado:
- melhor coerência entre manifest de evidência e avaliação
- menos ambiguidade em cenários de testes/logs/implementação

Arquivos-alvo prováveis:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/evaluator/evaluator.py`
- testes correspondentes

### Item 3 — métricas com sinal de execução externa quando houver

Fazer `metrics` reconhecer dispatch/execução externa registrados na run quando existirem.

Resultado esperado:
- enriquecer rounds, custo e falhas por tipo com base em eventos externos
- manter fallback atual quando esse sinal não existir

Arquivos-alvo prováveis:
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `src/cvg_harness/types.py`
- `src/cvg_harness/operator/service.py`

Resultado esperado:
- `metrics` passa a expor o total de sinais externos e uma quebra mínima entre solicitado, planejado, despachado e falho
- o dashboard reaproveita o mesmo breakdown quando ele existir no event log

## Critérios de saída

- existe hand-off explícito para executor externo sem automação cega
- `inspect` mostra o plano de execução externa quando ele existir
- evaluator passa a reconhecer parte do schema estruturado de evidência
- métricas continuam verdes no fluxo atual e melhoram quando houver execução externa registrada
- documentação continua honesta sobre limites

## Validação mínima

```bash
pytest -q
python3 examples/demo_complete_flow.py
python3 -m cvg_harness --help
```

## Fechamento

Verificação de código desta sprint mostrou que o documento havia sido fechado cedo demais: o item 1 já estava funcional, mas o item 2 ainda dependia do wiring real entre `OperatorService -> FlowOrchestrator -> Evaluator`, e o item 3 ainda tinha inconsistência no `MetricsAggregator`.

Estado final validado:
- `done` item 1: hand-off explícito para executor externo registrado na run e exposto em `inspect`
- `done` item 2: evaluator reconhecendo `kind`, `ref` e `module` no fluxo operador real, sem depender só do flatten textual
- `done` item 3: métricas reconhecendo sinais de execução externa e expondo breakdown mínimo sem quebrar o demo

Validação executada nesta rodada:
- `pytest -q` → `225 passed`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`
- `python3 -m cvg_harness --help` → help operador-first preservado
