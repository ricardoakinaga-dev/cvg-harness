# 0037. Relatório de auditoria pós-Sprint 15

## Objetivo
Registrar o estado real do `cvg-harness` após as Sprints 14 e 15, recalibrando principalmente `SpecBuilderAgent`, contratos da SPEC e a camada de métricas operacionais canônicas à luz da implementação atual, da suíte de testes e do demo principal.

## Evidências executadas
```bash
pytest -q
pytest --collect-only -q
python3 examples/demo_complete_flow.py
pytest -q tests/test_agents_extended.py tests/test_pr03_flow_orchestrator.py -rA
```

Resultado observado nesta auditoria:
- `pytest -q` -> `189/189` testes passando
- `pytest --collect-only -q` -> `189 tests collected`
- `examples/demo_complete_flow.py` -> `APPROVED`, `10/10` gates persistidos, `pass rate 100%`, `Fluxo: completed`
- suíte focal de métricas/orchestrator -> `31/31` testes passando

## Leitura executiva
O projeto saiu de um estado “planning mais realista, mas analytics ainda raso” para um estado mais coerente entre upstream, contratos da SPEC e leitura operacional do workspace. O principal ganho desta rodada está em duas frentes:
- a SPEC passou a carregar contratos minimamente priorizados por risco, com `criticidade`, `superficie` e `evidencia_minima`;
- a camada de métricas agora consegue materializar `delivery-metrics.json` canônico a partir de eventos e progresso reais, inclusive sob demanda no REPL.

O principal gap remanescente já não está em planning básico nem em contrato mínimo de entrega. O espaço de melhoria migrou para profundidade de observabilidade P2, maior rigor em `Architecture Guardian` e `Drift Detector` e capacidades P3 ainda declaradas mais do que exercitadas.

## Achados principais

### 1. SPEC agora diferencia melhor contratos críticos de contratos auxiliares
Severidade: resolvido

Estado atual:
- `SpecBuilderAgent` gera contratos com `criticidade`, `superficie` e `evidencia_minima`;
- contextos sensíveis como `auth`, `api`, `database` e `release` passam a nascer com maior priorização por risco;
- `observabilidade` e `rollback` ficaram menos genéricos quando o contexto observado permite resposta mais operacional.

Impacto:
- reduz a distância entre SPEC “válida” e SPEC “útil para handoff real”;
- melhora a qualidade do downstream para lint, planner, evaluator e leitura humana.

Arquivos centrais:
- `src/cvg_harness/spec_builder/spec_builder.py`
- `tests/test_agents.py`
- `tests/test_pr02_canonical_artifacts.py`
- `tests/test_pr03_flow_orchestrator.py`

### 2. Métricas operacionais ganharam caminho canônico de materialização
Severidade: resolvido

Estado atual:
- `MetricsAggregator` exporta `delivery-metrics.json` no contrato canônico documentado;
- o cálculo parte de `event-log.jsonl` e `progress.json` reais quando disponíveis;
- o REPL consegue gerar métricas sob demanda no workspace mesmo quando o artefato ainda não existe.

Impacto:
- a leitura operacional deixa de depender só do demo ou de inspeção manual do event log;
- a camada P2 de analytics fica menos aspiracional e mais exercitável no produto real.

Arquivos centrais:
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `src/cvg_harness/metrics/metrics_catalog.py`
- `src/cvg_harness/repl.py`
- `tests/test_agents_extended.py`

### 3. Núcleo aprovado segue estável após as melhorias incrementais
Severidade: confirmado

Estado atual:
- demo principal continua encerrando com `Release: APPROVED` e `Fluxo: completed`;
- o total da suíte subiu para `189` sem reabrir regressões estruturais;
- o fluxo fim a fim preserva gates, progress, artefatos canônicos e release readiness.

Impacto:
- as melhorias das Sprints 14 e 15 foram incrementais de verdade, sem reabrir o núcleo estabilizado em Sprints anteriores.

Arquivos centrais:
- `src/cvg_harness/flow.py`
- `src/cvg_harness/release/release_readiness.py`
- `examples/demo_complete_flow.py`

## Notas por item analisado

### Núcleo operacional
- Visão geral / tese operacional: `89/100`
- Classificação FAST vs ENTERPRISE: `92/100`
- Research Engine: `74/100`
- PRD Engine: `78/100`
- Spec Builder: `87/100`
- Contratos de artefatos: `91/100`
- Spec Linter: `90/100`
- Sprint Planner: `81/100`
- Flow Orchestrator fim a fim: `87/100`
- Gates e política de aprovação: `87/100`
- Fallback e replanejamento: `85/100`
- Architecture Guardian: `77/100`
- Evaluator / QA Gate: `78/100`
- Drift Detector: `76/100`
- Release Readiness: `86/100`
- Progress Ledger + Event Log: `84/100`
- Runtime / hooks operacionais: `85/100`
- Metrics Aggregator: `86/100`

### Produto, documentação e extensões
- README + demos + examples: `89/100`
- Capacidades P2 de observabilidade/analytics: `78/100`
- Capacidades P3 estratégicas: `50/100`
- Aderência documental geral: `88/100`

## Nota global
`87/100`

## Diferença em relação à auditoria 0034
- `Spec Builder`: `81 -> 87`
- `Contratos de artefatos`: `88 -> 91`
- `Metrics Aggregator`: `74 -> 86`
- `Capacidades P2 de observabilidade/analytics`: `68 -> 78`
- `README + demos + examples`: `88 -> 89`
- `Nota global`: `84 -> 87`

## Próximo passo recomendado
Abrir um sprint curto focado em uma destas frentes, sem reabrir planning, contratos básicos ou métricas canônicas já estabilizadas:
1. endurecimento de `Architecture Guardian` e `Drift Detector` para cenários mais ricos;
2. observabilidade P2 mais profunda sobre causalidade de gates, rounds e bloqueios;
3. redução de heurística residual em `Evaluator` para evidências negativas e exceções mais fortes.

## Encadeamento
- Auditoria histórica anterior: `docs/0034-relatorio-de-auditoria-pos-sprint-12.md`
- Sprint 14: `docs/0035-sprint-14-contratos-criticos-no-spec-builder.md`
- Sprint 15: `docs/0036-sprint-15-metricas-operacionais-canônicas.md`
- Próximo ciclo incremental aberto em `docs/0038-sprint-16-endurecimento-guardian-drift.md`.
