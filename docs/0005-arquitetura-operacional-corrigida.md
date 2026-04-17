# 0005. Arquitetura operacional corrigida

## Visão geral
A arquitetura corrigida do `cvg-harness` é composta por 14 blocos.

## 1. Intake & Classification Layer
### Função
Receber a demanda, clarificar contexto mínimo e definir modo FAST ou ENTERPRISE.
### Entradas
brief, issue, pedido, contexto inicial.
### Saídas
`intake.md`, `classification.json`.
### Dependências
nenhuma.
### Critério para avançar
demanda classificada com score e racional.
### Risco se falhar
todo o fluxo seguinte roda no modo errado.

## 2. Research Engine
### Função
Mapear arquitetura atual, arquivos relevantes, decisões existentes, riscos e restrições.
### Entradas
`intake.md`, `classification.json`, codebase.
### Saídas
`research-notes.md`, `system-map.md`.
### Dependências
classificação concluída.
### Critério para avançar
módulos impactados e riscos principais identificados.
### Risco se falhar
SPEC nasce cega e incompleta.

## 3. PRD Engine
### Função
Converter necessidade em definição de problema, objetivo, escopo e sucesso.
### Entradas
intake, classification, research.
### Saídas
`prd.md`.
### Critério para avançar
objetivo, escopo, fora de escopo e sucesso definidos.
### Risco se falhar
execução tecnicamente correta para problema errado.

## 4. Spec Builder
### Função
Traduzir PRD e research em especificação técnica executável.
### Entradas
`prd.md`, `research-notes.md`, `system-map.md`.
### Saídas
`spec.md`, `spec.json`.
### Critério para avançar
SPEC com critérios testáveis (ou lacunas explícitas), limites claros, contratos identificados e módulos afetados definidos.
### Risco se falhar
coder interpreta demais.

## 5. Spec Linter
### Função
Validar a qualidade executável da SPEC antes da codificação.
### Entradas
`spec.md`, `spec.json`.
### Saídas
`spec-lint-report.json`.
### Critério para avançar
nenhuma falha bloqueante.
### Risco se falhar
erro de planejamento vaza para a execução.

## 6. Sprint Planner
### Função
Quebrar a SPEC em unidades pequenas, sequenciadas e executáveis.
### Entradas
SPEC aprovada e lintada.
### Saídas
`sprint-plan.json`, `execution-order.json`.
### Critério para avançar
cada sprint tem escopo fechado, dono, dependência e evidência esperada.
### Risco se falhar
execução vira mar aberto.

## 7. Execution Orchestrator
### Função
Despachar sprint para o agente correto, controlar sequência e consolidar estado.
### Entradas
`execution-order.json`, `sprint-plan.json`, `progress.json`.
### Saídas
transições de estado e handoffs.
### Critério para avançar
somente uma sprint ativa por fluxo.
### Risco se falhar
concorrência indevida, perda de rastreabilidade.

## 8. Architecture Guardian
### Função
Bloquear desvios arquiteturais durante a execução.
### Entradas
SPEC, sprint ativa, mudanças propostas.
### Saídas
`architecture-guard-report.json`.
### Critério para avançar
nenhum desvio estrutural não autorizado.
### Risco se falhar
débito técnico vira produto.

## 9. Coder Worker
### Função
Executar apenas a sprint autorizada.
### Entradas
sprint ativa, handoff, limites permitidos.
### Saídas
implementação e evidências da sprint.
### Critério para avançar
entrega restrita ao escopo e evidências mínimas anexadas.
### Risco se falhar
escopo explode ou execução inventa comportamento.

## 10. Evaluator / QA Gate
### Função
Avaliar a sprint contra critérios, evidências e contratos.
### Entradas
implementação, SPEC, sprint plan, evidências.
### Saídas
`evaluation-report.json`.
### Critério para avançar
todos os critérios obrigatórios aprovados ou waiver formal.
### Risco se falhar
sprint ruim é promovida.

## 11. Drift Detector
### Função
Detectar desalinhamento entre intenção, plano e execução.
### Entradas
intake, PRD, SPEC, sprint plan, avaliação e documentação final.
### Saídas
`drift-report.json`.
### Critério para avançar
drift zerado ou aceito formalmente.
### Risco se falhar
o sistema entrega outra coisa e ninguém percebe.

## 12. Progress Ledger / Event Log
### Função
Registrar estado corrente e eventos operacionais.
### Entradas
decisões e transições do fluxo.
### Saídas
`progress.json`, `event-log.jsonl`.
### Critério para avançar
evento crítico sempre registrado.
### Risco se falhar
não há auditoria nem analytics.

## 13. Release Readiness Engine
### Função
Decidir se a entrega está pronta para promoção.
### Entradas
avaliações, drift, progress, evidências.
### Saídas
`release-readiness-report.json` como artefato canônico de máquina, com `release-readiness.md` como sidecar opcional legível por humano.
### Critério para avançar
todos os gates finais aprovados.
### Risco se falhar
promoção sem prontidão real.

## 14. Delivery Intelligence / Metrics Layer
### Função
Consolidar métricas para melhoria contínua.
### Entradas
ledger, event log, relatórios.
### Saídas
`delivery-metrics.json` e indicadores.
### Critério para avançar
dados mínimos coletados por sprint.
### Risco se falhar
não há aprendizado operacional.
