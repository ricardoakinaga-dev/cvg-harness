# 0013. Roadmap de implementação

## Fase 0 — Correção estrutural do planejamento
### Objetivo
Fechar o desenho operacional correto antes do código do produto.
### Entregas
- auditoria crítica
- arquitetura corrigida
- contratos de artefatos
- gates formais
- fallback formal

## Fase 1 — Núcleo mínimo executável
### Objetivo
Tornar o fluxo operável de forma manual, porém rigorosa.
### Entregas
- `classification.json`
- `progress.json`
- `event-log.jsonl`
- templates de PRD, SPEC e sprint plan
- decisão FAST vs ENTERPRISE

## Fase 2 — Qualidade de planejamento
### Objetivo
Reduzir erro antes do código.
### Entregas
- Spec Linter
- contratos fortes de handoff
- catálogo de evidências
- tipologia de falhas

## Fase 3 — Controle de execução
### Objetivo
Proteger arquitetura e reduzir deriva.
### Entregas
- Architecture Guardian
- Drift Detector
- Replan Coordinator
- política de exceção e waiver

## Fase 4 — Observabilidade e métricas
### Objetivo
Transformar operação em sistema gerenciável.
### Entregas
- métricas consolidadas
- analytics por sprint
- custo e retrabalho por agente
- indicadores executivos

## Fase 5 — Integração com execução real
### Objetivo
Conectar o plano ao runtime.
### Entregas
- hooks para lint, typecheck e testes
- ingestão de evidências externas
- integração com CI/CD

