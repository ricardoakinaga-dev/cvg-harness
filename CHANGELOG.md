# Changelog

## [0.1.0] - 2026-04-16

### Added

#### P0 - Crítico
- `classification/classifier.py` — Classificador FAST vs ENTERPRISE com 8 dimensões
- `contracts/artifact_contracts.py` — Contratos de 17 artefatos com campos obrigatórios
- `linter/spec_linter.py` — Spec Linter com regras bloqueantes e score 0-100
- `guardian/architecture_guardian.py` — Architecture Guardian com verificação de áreas
- `drift/drift_detector.py` — Drift Detector para 6 camadas de comparação
- `gates/gate_policy.py` — 10 gates (GATE_0 a GATE_9) com critérios objetivos
- `fallback/fallback_policy.py` — Política de falha 1/2/3 com replan e waiver

#### Agentes (completos)
- `research/research_agent.py` — Research Agent: gera research-notes.md e system-map.md
- `prd/prd_agent.py` — PRD Agent: gera prd.md a partir de research
- `spec_builder/spec_builder.py` — Spec Builder Agent: gera spec.md e spec.json
- `coder/coder_worker.py` — Coder Worker: executa sprint com validação de escopo
- `replan/replan_coordinator.py` — Replan Coordinator: coordena replanejamento formal
- `metrics_agg/metrics_aggregator.py` — Metrics Aggregator: consolida métricas

#### P1 - Alto
- `ledger/progress_ledger.py` — Progress Ledger com estado vivo
- `ledger/event_log.py` — Event Log append-only
- `metrics/metrics_catalog.py` — Catálogo de métricas de entrega
- `contracts/handoff.py` — Contratos de handoff entre agentes
- `templates/revised_templates.py` — Templates para PRD, SPEC e Sprint Plan
- `sprint/sprint_planner.py` — Sprint Planner (quebra SPEC em sprints fechadas)
- `evaluator/evaluator.py` — Evaluator / QA Gate
- `release/release_readiness.py` — Release Readiness Engine

#### P2 - Médio
- `dashboard/dashboards.py` — Geração de dashboard a partir de ledger
- `agent_scoring/agent_scores.py` — Scoring de performance por agente
- `sprint_history/sprint_history.py` — Histórico comparativo de sprints
- `patterns/patterns_library.py` — Biblioteca de 7 padrões reutilizáveis

#### P3 - Futuro
- `orchestration/multi_project.py` — Orquestração multi-projeto
- `domain_optimization/domain_optimizer.py` — Otimização por domínio
- `comparative_intelligence/comparators.py` — Inteligência comparativa cross-projeto
- `auto_runtime/runtime_automation.py` — Automação de runtime com hooks

#### Infraestrutura
- `flow.py` — Flow Orchestrator conectando Intake → Release
- `repl.py` — REPL interativo com 12 comandos
- `cli/cli.py` — CLI com 8 subcomandos e error handling
- `__main__.py` — Entry point para `python -m cvg_harness`
- `types.py` — Tipos e constantes compartilhadas
- Entry points `cvg` e `cvg-repl` no pyproject.toml
- `setup.cfg` — Configuração pytest, mypy, flake8
- `.gitignore` — Ignora pycache, venv, pytest_cache, etc.
- `Makefile` — Targets: install, test, coverage, demo, clean
- `CONTRIBUTING.md` — Guia de contribuição

#### Testes
- 90 testes cobrindo: classifier, linter, drift, fallback, progress, flow, guardian, handoff, sprint_planner, evaluator, release, integration, agents, coder, replan, metrics_agg

#### Exemplos (10)
- `examples/example_classification.py` — Classificação FAST
- `examples/example_enterprise.py` — Classificação ENTERPRISE
- `examples/example_spec_lint.py` — Lint de SPEC
- `examples/example_flow.py` — Fluxo completo
- `examples/example_sprint_planner.py` — Sprint Planner
- `examples/example_evaluator_release.py` — Evaluator e Release Readiness
- `examples/example_agents.py` — Coder Worker, Replan Coordinator, Metrics Aggregator
- `examples/example_research_prd_spec.py` — Research → PRD → Spec Builder
- `examples/demo_complete_flow.py` — Demo end-to-end completo
- `examples/cvg_harness_demo.ipynb` — Jupyter notebook interativo
