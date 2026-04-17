# 0014. Backlog priorizado

## P0 — Crítico
### 1. Classificador FAST vs ENTERPRISE
- definir score e override
- gerar `classification.json`

### 2. Contratos mais fortes
- revisar `spec.json`
- incluir áreas autorizadas e proibidas
- definir handoff mínimo

### 3. Spec Linter
- regras bloqueantes
- score de qualidade executável

### 4. Architecture Guardian
- políticas de boundary e escopo

### 5. Drift Detector
- comparação entre camadas do fluxo

### 6. Gates corrigidos
- estados formais
- critérios objetivos

### 7. Fallback formal
- política de falha 1, 2, 3
- regras de replan e waiver

## P1 — Alto
### 1. Progress ledger evoluído
### 2. Event log append-only
### 3. Catálogo de métricas
### 4. Contratos de handoff entre agentes
### 5. Templates revisados

## P2 — Médio
### 1. Dashboards canônicos
- `dashboard.json` como visão operacional derivada
### 2. Scoring por agente
### 3. Histórico comparativo de sprints
### 4. Biblioteca de padrões reutilizáveis

## P3 — Futuro
### 1. Orquestração ampla multi-projeto
### 2. Otimização por domínio
### 3. Inteligência comparativa entre projetos
### 4. automação mais profunda do runtime

## Ordem recomendada
P0 primeiro, depois P1. P2 e P3 só fazem sentido quando os contratos básicos estiverem estáveis.
