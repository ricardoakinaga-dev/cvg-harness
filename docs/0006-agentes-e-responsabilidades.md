# 0006. Agentes e responsabilidades

## Regra geral
Todo agente no `cvg-harness` tem missão, entrada, saída, limites e evidência obrigatória. Nenhum agente deve assumir responsabilidades implícitas.

## 1. Intake Classifier Agent
### Missão
Classificar a demanda e selecionar modo operacional.
### Não faz
planejamento técnico profundo, codificação.
### Saída
`classification.json`.

## 2. Research Agent
### Missão
Explorar o sistema e reduzir cegueira técnica.
### Saída
`research-notes.md`, `system-map.md`.
### Falha típica
confundir hipótese com fato.

## 3. PRD Agent
### Missão
Formalizar o problema de produto e os limites de negócio.
O PRD deriva problema, escopo e critérios de aceite a partir de `research-notes`, com riscos e módulos reais da análise inicial.
### Saída
`prd.md`.

## 4. Spec Builder Agent
### Missão
Gerar instrução técnica executável.
### Saída
`spec.md`, `spec.json`.
### Regra
não pode deixar critério não testável sem marcar como lacuna.

## 5. Spec Linter Agent
### Missão
Detectar ambiguidade, lacunas e inconsistências antes da execução.
### Checa
- critérios não testáveis
- edge cases ausentes
- módulos vagos
- contratos incompletos
- contradições internas
### Saída
`spec-lint-report.json`.

## 6. Sprint Planner Agent
### Missão
Quebrar a SPEC em sprints executáveis.
### Saída
`sprint-plan.json`, `execution-order.json`.

## 7. Execution Orchestrator Agent
### Missão
Controlar handoff, ordem de execução, atualização de estado e bloqueios.
### Regra
não permite mais de uma sprint ativa no mesmo fluxo sem política explícita.

## 8. Architecture Guardian Agent
### Missão
Impedir desvio arquitetural.
### Checa
- violação de domínio
- acoplamento indevido
- mudança estrutural fora do escopo
- criação de débito técnico não autorizado
### Saída
`architecture-guard-report.json`.

## 9. Coder Worker Agent
### Missão
Executar a sprint autorizada.
### Regra
não redefine produto, não amplia escopo, não altera zona proibida.
### Evidência mínima
arquivos alterados, racional curto, evidências definidas na sprint.

## 10. Evaluator Agent
### Missão
Validar resultado com independência.
### Checa
- critérios de aceite
- contratos
- edge cases previstos
- evidências obrigatórias
### Saída
`evaluation-report.json`.

## 11. Drift Detector Agent
### Missão
Detectar desalinhamento entre artefatos e execução.
### Saída
`drift-report.json`.

## 12. Replan Coordinator Agent
### Missão
Acionar replanejamento formal quando o plano deixa de sustentar a execução.
### Gatilhos
- falha recorrente do evaluator
- SPEC insuficiente
- sprint superdimensionada
- drift grave
- classificação errada
### Saída
decisão de replan, atualização de artefatos, novo plano.

## 13. Release Readiness Agent
### Missão
Consolidar decisão final de prontidão.
### Saída
`release-readiness-report.json` como saída canônica, com `release-readiness.md` opcional como espelho legível para humano.

## 14. Metrics Aggregator Agent
### Missão
Consolidar dados para gestão e melhoria contínua.
### Saída
`delivery-metrics.json`.
### Visualização derivada
`dashboard.json` como sidecar operacional derivado de `progress.json`, `event-log.jsonl` e `delivery-metrics.json`.

## Contrato de handoff entre agentes
Todo handoff deve carregar:
- artefato fonte
- versão do artefato
- objetivo da próxima etapa
- restrições válidas
- dúvidas abertas
- evidências exigidas na saída
