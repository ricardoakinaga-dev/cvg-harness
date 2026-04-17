# 0007. Contratos dos artefatos

## Política geral
Todo artefato tem:
- objetivo
- responsável por gerar
- momento de criação
- regras de mutação
- aprovador
- campos obrigatórios
- relação com artefatos vizinhos
- versão

## 1. `intake.md`
- **objetivo:** registrar a demanda inicial
- **gera:** Intake Classifier
- **nasce:** recebimento da demanda
- **pode mudar:** até Gate 0
- **aprova:** owner da demanda
- **campos:** problema, contexto, urgência, impacto, premissas, perguntas

## 2. `classification.json`
- **objetivo:** classificar complexidade e modo
- **gera:** Intake Classifier
- **nasce:** após intake
- **pode mudar:** por reclassificação formal
- **aprova:** planner responsável
- **campos:** score por dimensão, modo, racional, override, aprovador, timestamp

## 3. `research-notes.md`
- **objetivo:** consolidar fatos técnicos, riscos e restrições
- **gera:** Research Agent
- **nasce:** após classificação
- **pode mudar:** até Gate 1
- **aprova:** planner técnico
- **campos:** fatos, hipóteses, riscos, dependências, dúvidas

## 4. `system-map.md`
- **objetivo:** mapear módulos, boundaries e superfícies afetadas
- **gera:** Research Agent
- **nasce:** durante research
- **pode mudar:** até Gate 1
- **aprova:** planner técnico
- **campos:** módulos, dependências, zonas críticas, arquivos/áreas prováveis

## 5. `prd.md`
- **objetivo:** definir problema, objetivo, sucesso e limites de negócio
- **gera:** PRD Agent
- **nasce:** após research
- **pode mudar:** até Gate 2 ou por replan formal
- **aprova:** owner de produto
- **campos:** problema, objetivo, KPIs, escopo, fora de escopo, user stories, riscos

## 6. `spec.md`
- **objetivo:** especificação legível para humanos
- **gera:** Spec Builder
- **nasce:** após PRD
- **pode mudar:** até Gate 3 ou por replan formal
- **aprova:** planner técnico
- **campos:** objetivo técnico, módulos afetados, contratos com criticidade/superfície/evidência mínima, regras, fluxos, erros, limites, critérios (com lacunas explicitadas quando não testáveis), testes, observabilidade e rollback contextual

## 7. `spec.json`
- **objetivo:** especificação determinística para agentes e orquestração
- **gera:** Spec Builder
- **nasce:** junto com `spec.md`
- **pode mudar:** em sincronia com `spec.md`
- **aprova:** planner técnico
- **campos mínimos:** meta, módulos, áreas autorizadas, áreas proibidas, contratos priorizados por risco, sprints, critérios, edge cases, observabilidade, rollback

## 8. `spec-lint-report.json`
- **objetivo:** registrar qualidade executável da SPEC
- **gera:** Spec Linter
- **nasce:** após SPEC
- **pode mudar:** a cada rerun do lint
- **aprova:** automático + revisão humana quando bloqueante
- **campos:** resultado, falhas, warnings, score, recomendação

## 9. `sprint-plan.json`
- **objetivo:** quebrar a SPEC em sprints fechadas
- **gera:** Sprint Planner
- **nasce:** após lint aprovado
- **pode mudar:** por replan formal
- **aprova:** planner técnico
- **campos:** sprints, dependências, agente alvo, critérios, evidências, risco

## 10. `execution-order.json`
- **objetivo:** definir ordem de promoção e pré-condições
- **gera:** Sprint Planner / Orchestrator
- **nasce:** após sprint plan
- **pode mudar:** por replan formal
- **aprova:** orchestrator owner
- **campos:** sequência, bloqueios, paralelismo permitido, pré-condições

## 11. `architecture-guard-report.json`
- **objetivo:** registrar aderência arquitetural da sprint
- **gera:** Architecture Guardian
- **nasce:** durante/ao final da sprint
- **pode mudar:** a cada revalidação
- **aprova:** architecture owner ou waiver formal
- **campos:** resultado, desvios, severidade, áreas afetadas, decisão

## 12. `evaluation-report.json`
- **objetivo:** registrar resultado da validação funcional/técnica
- **gera:** Evaluator
- **nasce:** após entrega da sprint
- **pode mudar:** a cada novo round
- **aprova:** evaluator lead
- **campos:** sprint_id, spec_ref, result, criterion_results, criterios, status, evidencias, falhas, evidence_provided, evidence_missing, structured_evidence_count, structured_evidence_summary, next_action, round, timestamp

## 13. `drift-report.json`
- **objetivo:** medir desalinhamento entre artefatos e execução
- **gera:** Drift Detector
- **nasce:** após avaliação ou antes de release
- **pode mudar:** a cada rodada de detecção
- **aprova:** planner técnico
- **campos:** drift por camada, severidade, causa provável, ação requerida

## 14. `progress.json`
- **objetivo:** estado vivo da execução
- **gera:** Orchestrator
- **nasce:** ao abrir o fluxo
- **pode mudar:** durante toda a execução
- **aprova:** sistema/orchestrator
- **campos:** modo, sprint atual, status, rounds, bloqueios, métricas, aprovações

## 15. `event-log.jsonl`
- **objetivo:** trilha imutável de eventos
- **gera:** Orchestrator e motores de gate
- **nasce:** no início do fluxo
- **pode mudar:** apenas append
- **aprova:** não se aplica, mas não pode ser reescrito silenciosamente
- **campos:** timestamp, event_type, actor, artifact_ref, metadata

## 16. `release-readiness-report.json` + `release-readiness.md`
- **objetivo:** consolidar decisão final de prontidão
- **gera:** Release Readiness Engine
- **nasce:** ao fim das sprints
- **pode mudar:** até Gate 9
- **aprova:** owner técnico e owner de release
- **modelo:** JSON canônico (`release-readiness-report.json`) + sidecar MD legível para humanos (`release-readiness.md`)
- **campos obrigatórios (JSON):** project, feature, decision, gates_summary, missing_gates, exceptions, residual_risks, waivers, timestamp
- **campos opcionais (MD):** resumo, gates, exceções, riscos residuais, decisão
- **nota:** o artefato JSON é o canônico para consumo por máquinas e gates. O MD é gerado opcionalmente para leitura humana.

## 17. `delivery-metrics.json`
- **objetivo:** métricas para gestão e melhoria
- **gera:** Metrics Aggregator
- **nasce:** após primeiro ciclo de entrega
- **pode mudar:** continuamente
- **aprova:** gestão técnica
- **campos:** lead time, rounds, retry rounds, pass rate, retrabalho, custo, falhas por tipo, sprints count, gates blocked, structural blockers, replan events, waiver events, external execution signals, external execution breakdown, runtime provider breakdown

## 18. `external-dispatch-plan.json`
- **objetivo:** registrar o plano formal de dispatch externo opt-in
- **gera:** Operator Service + ExternalExecutorBridge
- **nasce:** quando o operador prepara handoff para executor externo
- **pode mudar:** a cada novo planejamento de dispatch
- **aprova:** operador
- **campos:** run_id, sprint_id, adapter, provider, status, planned_command, context, context_sources, context_hints, required_context, missing_context_hints, missing_required_context, available_context_keys, capability, policy_source, active_policy, selection_reason, suitability_score, alternative_adapters, execute, metadata, request_metadata, result_metadata, runtime_profile, runtime_provider
- **nota:** sidecar operacional para planejamento e inspeção; antecede o resultado do dispatch

## 19. `external-dispatch-result.json`
- **objetivo:** registrar o resultado formal de um dispatch externo opt-in
- **gera:** ExternalExecutorBridge
- **nasce:** após planejamento ou despacho externo
- **pode mudar:** a cada novo dispatch
- **aprova:** operador e executor externo quando aplicável
- **campos:** adapter, status, planned_command, external_ref, evidence_refs, notes, metadata, context_sources, runtime_profile, runtime_provider, request_metadata, created_at
- **nota:** sidecar operacional; não substitui `progress.json` nem `event-log.jsonl`

## 20. `runtime-hooks.json`
- **objetivo:** registrar hooks de runtime executados e seus resultados
- **gera:** Runtime Executor
- **nasce:** quando hooks de runtime forem disparados pelo operador
- **pode mudar:** a cada nova execução
- **aprova:** operador
- **campos:** run_id, event, profile, provider, simulated, context, raw_context, resolved_context, context_hints, required_context, missing_context_hints, missing_required_context, available_context_keys, results, external_evidence_refs, updated_at
- **nota:** sidecar operacional para runtime opt-in; não vira fonte de verdade do fluxo

## 21. `external-evidence-manifest.json`
- **objetivo:** registrar referências de evidência externa derivadas de runtime/handoff
- **gera:** Runtime Executor / Operator Service
- **nasce:** quando houver refs externas observáveis
- **pode mudar:** a cada nova coleta de evidência
- **aprova:** operador
- **campos:** run_id, event, simulated, evidence_refs, results, updated_at
- **nota:** sidecar operacional complementar a `runtime-hooks.json`

## 22. `ci-result.json`
- **objetivo:** registrar o resumo operacional de um resultado de CI derivado de runtime opt-in
- **gera:** Runtime Executor / Operator Service
- **nasce:** quando o runtime processa o evento `ci_result`
- **pode mudar:** a cada nova coleta/execução de CI
- **aprova:** operador
- **campos:** run_id, event, profile, provider, simulated, context, raw_context, status, ci_ref, evidence_refs, results, source, metadata, updated_at
- **nota:** sidecar operacional; não substitui gates ou release readiness por si só

## 23. `dashboard.json`
- **objetivo:** materializar a visão operacional consolidada do fluxo
- **gera:** Dashboard
- **nasce:** quando progress/event/metrics estão disponíveis
- **pode mudar:** continuamente
- **aprova:** gestão técnica e operação
- **campos:** project, feature, mode, status, current_gate, current_sprint, gates_summary, event_counts, metrics_summary, blockers, recent_events, generated_at
- **nota:** sidecar operacional de visualização; agrega `runtime_provider_breakdown` em `metrics_summary`

## 24. `delivery-metrics.json` detalhado
- **objetivo:** consolidar métricas operacionais com quebra por provider
- **gera:** Metrics Aggregator
- **nasce:** após agregação do ledger e do event log
- **pode mudar:** continuamente
- **aprova:** gestão técnica
- **campos:** lead time, rounds, retry rounds, pass rate, retrabalho, custo, falhas por tipo, sprints count, gates blocked, structural blockers count, structural blockers, replan events, waiver events, external execution signals, external execution breakdown, runtime provider breakdown
- **nota:** versão mais detalhada do contrato de métricas para leitura operacional e dashboard

## Política de versionamento
- todo artefato mutável deve ter `version`
- mudança após aprovação exige `change_reason`
- replan formal deve referenciar artefatos substituídos
