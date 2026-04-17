# 0034. Relatório de auditoria pós-Sprint 12

## Objetivo
Registrar o estado real do `cvg-harness` após o fechamento da Sprint 12, recalibrando principalmente os motores de planning (`ResearchAgent`, `PRDAgent`, `SpecBuilderAgent`) à luz da implementação atual, da suíte de testes e do demo principal.

## Evidências executadas
```bash
pytest -q
python3 examples/demo_complete_flow.py
```

Resultado observado nesta auditoria:
- `pytest -q` -> `184/184` testes passando
- `examples/demo_complete_flow.py` -> `APPROVED`, `10/10` gates persistidos, `pass rate 100%`, `Fluxo: completed`

## Leitura executiva
O projeto saiu de um estado “núcleo estável com upstream simplificado” para um estado mais coerente entre planejamento e execução. O ganho principal desta rodada está em `research -> PRD -> spec`: agora existe mais evidência real de codebase, mais variação material entre contextos diferentes e melhor cobertura de regressão provando esse comportamento.

O principal gap remanescente já não é mais fechamento de ciclo nem planning básico. O espaço de melhoria migrou para profundidade adicional de contratos, analytics/observabilidade P2 e capacidades estratégicas P3.

## Achados principais

### 1. Motores de planning deixaram de ser puramente heurísticos
Severidade: resolvido parcialmente / avanço forte

Estado atual:
- `ResearchAgent` agora inspeciona `workspace` e, quando necessário, cai para o repositório local para identificar módulos, áreas e boundaries reais;
- `PRDAgent` agora deriva problema, objetivo, escopo, riscos e critérios de aceite a partir de `research_notes` e `classification`;
- `SpecBuilderAgent` já nasce com contratos mínimos por contexto e critérios explicitamente marcados como lacuna quando ainda não são testáveis.

Atualização posterior:
- a criticidade contratual passou a ser endereçada na `docs/0035-sprint-14-contratos-criticos-no-spec-builder.md`, com contratos priorizados por risco e observabilidade/rollback mais específicos.

Impacto:
- reduz diferença entre docs fundacionais e comportamento real do upstream;
- melhora a qualidade do handoff para lint, sprint planning e avaliação.

Arquivos centrais:
- `src/cvg_harness/research/research_agent.py`
- `src/cvg_harness/prd/prd_agent.py`
- `src/cvg_harness/spec_builder/spec_builder.py`

### 2. Contrato vivo de planning agora está melhor provado na suíte
Severidade: resolvido

Estado atual:
- há cobertura unitária e de integração provando que `research`, `PRD` e `spec` mudam quando o contexto real do workspace muda;
- `tests/test_pr03_flow_orchestrator.py` já amarra o fluxo real até `build_spec()` com contexto observado do repositório.

Impacto:
- o comportamento dos motores de planning deixa de ser implícito;
- a próxima auditoria pode medir regressão de profundidade com base em testes, não só leitura manual de código.

Arquivos centrais:
- `tests/test_agents.py`
- `tests/test_pr02_canonical_artifacts.py`
- `tests/test_pr03_flow_orchestrator.py`
- `tests/test_linter.py`

### 3. Núcleo operacional continua consistente após o aprofundamento upstream
Severidade: confirmado

Estado atual:
- demo principal continua encerrando com `Release: APPROVED` e `Fluxo: completed`;
- gates, progress, release readiness e event log permanecem coerentes;
- a ampliação da suíte para `184` testes não reabriu regressões estruturais.

Impacto:
- o ganho de profundidade em planning não comprometeu a estabilidade do restante do sistema.

Arquivos centrais:
- `src/cvg_harness/flow.py`
- `src/cvg_harness/release/release_readiness.py`
- `examples/demo_complete_flow.py`

## Notas por item analisado

### Núcleo operacional
- Visão geral / tese operacional: `88/100`
- Classificação FAST vs ENTERPRISE: `92/100`
- Research Engine: `74/100`
- PRD Engine: `78/100`
- Spec Builder: `81/100`
- Contratos de artefatos: `88/100`
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
- Metrics Aggregator: `74/100`

### Produto, documentação e extensões
- README + demos + examples: `88/100`
- Capacidades P2 de observabilidade/analytics: `68/100`
- Capacidades P3 estratégicas: `50/100`
- Aderência documental geral: `86/100`

## Nota global
`84/100`

## Diferença em relação à auditoria 0028
- `Research Engine`: `48 -> 74`
- `PRD Engine`: `58 -> 78`
- `Spec Builder`: `63 -> 81`
- `Flow Orchestrator fim a fim`: `74 -> 87`
- `Release Readiness`: `74 -> 86`
- `Progress Ledger + Event Log`: `69 -> 84`
- `Nota global`: `76 -> 84`

## Próximo passo recomendado
Abrir um sprint curto focado em uma destas frentes, sem reabrir planning básico já resolvido:
1. profundidade de contratos e criticidade no `SpecBuilderAgent`
2. observabilidade/analytics P2 (`metrics_agg`, dashboards, leitura operacional)
3. endurecimento de `Architecture Guardian` e `Drift Detector` para cenários mais ricos

## Encadeamento
- Auditoria histórica anterior: `docs/0028-relatorio-de-auditoria-do-estado-real.md`
- Sprint que gerou esta melhora: `docs/0031-sprint-12-profundidade-dos-motores-de-planning.md`
- Sprint seguinte de contratos críticos: `docs/0035-sprint-14-contratos-criticos-no-spec-builder.md`
- Próximo ciclo incremental aberto em `docs/0035-sprint-14-contratos-criticos-no-spec-builder.md`.
