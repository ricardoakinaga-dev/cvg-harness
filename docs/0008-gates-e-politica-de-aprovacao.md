# 0008. Gates e política de aprovação

## Estado formal por gate
Cada gate deve ter um estado:
- `not_started`
- `in_review`
- `approved`
- `rejected`
- `waived`

## GATE 0 — Demanda classificada
- **objetivo:** definir modo operacional e risco inicial
- **entrada:** `intake.md`
- **saída:** `classification.json`
- **aprova se:** score e racional completos
- **reprova se:** modo sem justificativa ou classificação inconsistente
- **responsável:** Intake Classifier
- **fallback:** reclassificar ou escalar para ENTERPRISE

## GATE 1 — Research aprovado
- **objetivo:** garantir base factual mínima
- **entrada:** classification + codebase
- **saída:** `research-notes.md`, `system-map.md`
- **aprova se:** riscos, módulos e restrições principais identificados
- **reprova se:** pesquisa superficial ou baseada em hipótese não marcada
- **responsável:** Research Agent + planner técnico
- **fallback:** nova rodada de research

## GATE 2 — PRD aprovada
- **objetivo:** validar problema, objetivo e limites
- **entrada:** research
- **saída:** `prd.md`
- **aprova se:** escopo e sucesso estão claros
- **reprova se:** problema mal definido ou fora de escopo inconsistente
- **responsável:** owner de produto
- **fallback:** revisão de escopo

## GATE 3 — SPEC aprovada
- **objetivo:** validar executabilidade técnica inicial
- **entrada:** PRD + research
- **saída:** `spec.md`, `spec.json`
- **aprova se:** critérios, limites e contratos principais existem
- **reprova se:** SPEC vaga ou incompleta
- **responsável:** planner técnico
- **fallback:** voltar ao Spec Builder

## GATE 4 — Spec Lint aprovado
- **objetivo:** eliminar ambiguidade e lacunas executáveis
- **entrada:** SPEC
- **saída:** `spec-lint-report.json`
- **aprova se:** zero falha bloqueante
- **reprova se:** ambiguidade, critério não testável ou lacuna crítica
- **responsável:** Spec Linter
- **fallback:** corrigir SPEC e rerodar lint

## GATE 5 — Sprint pronta para execução
- **objetivo:** garantir que a sprint cabe em execução controlada
- **entrada:** SPEC aprovada e lintada
- **saída:** `sprint-plan.json`, `execution-order.json`
- **aprova se:** sprint tem escopo fechado, agente, evidências e dependências claras
- **reprova se:** sprint ampla demais ou sem evidência definida
- **responsável:** Sprint Planner
- **fallback:** quebrar sprint ou replan

## GATE 6 — Execução aderente à arquitetura
- **objetivo:** impedir desvio estrutural durante a implementação
- **entrada:** entrega da sprint
- **saída:** `architecture-guard-report.json`
- **aprova se:** nenhuma violação sem waiver
- **reprova se:** boundary quebrado, acoplamento indevido ou área proibida tocada
- **responsável:** Architecture Guardian
- **fallback:** correção obrigatória ou replan

## GATE 7 — Avaliação aprovada
- **objetivo:** validar a sprint contra critérios e evidências
- **entrada:** entrega + guard report
- **saída:** `evaluation-report.json`
- **aprova se:** critérios obrigatórios aprovados
- **reprova se:** falha funcional, contratual ou de evidência
- **responsável:** Evaluator
- **fallback:** retorno ao coder ou replan

## GATE 8 — Drift zerado ou aceito formalmente
- **objetivo:** garantir alinhamento entre intenção, plano e execução
- **entrada:** artefatos e avaliação
- **saída:** `drift-report.json`
- **aprova se:** drift inexistente ou waiver formal justificado
- **reprova se:** desalinhamento grave sem aceite formal
- **responsável:** Drift Detector + planner técnico
- **fallback:** replan ou correção documental/execução

## GATE 9 — Release readiness aprovada
- **objetivo:** consolidar prontidão para promoção
- **entrada:** todos os relatórios finais
- **saída:** `release-readiness-report.json` como canônico, com `release-readiness.md` opcional como sidecar
- **aprova se:** `GATE_0` a `GATE_8` fechados e riscos residuais aceitáveis
- **reprova se:** há bloqueio aberto, evidência faltante ou exceção sem dono
- **responsável:** Release Readiness Engine + owner técnico
- **fallback:** segurar release e corrigir bloqueios

