# 0011. Spec Lint, Architecture Guard e Drift Detector

## 1. Spec Lint
### Objetivo
Detectar defeitos de planejamento antes da execução.

### Regras mínimas de lint
- critério de aceite não testável -> bloqueante
- módulo afetado vago -> bloqueante
- ausência de edge cases -> bloqueante em ENTERPRISE, warning em FAST
- ausência de exemplos de payload/contrato -> bloqueante quando houver integração
- conflito interno entre `spec.md` e `spec.json` -> bloqueante
- ausência de limite de escopo -> bloqueante
- ausência de área proibida em mudança estrutural -> bloqueante
- ausência de rollback ou observabilidade em fluxo crítico -> bloqueante

### Saída
`spec-lint-report.json` com:
- resultado
- score
- falhas bloqueantes
- warnings
- sugestões

## 2. Architecture Guardian
### Objetivo
Impedir que a execução degrade a arquitetura.

### Regras mínimas
- mudança em boundary não autorizada -> bloqueante
- criação de dependência circular -> bloqueante
- acoplamento de domínio indevido -> bloqueante
- alteração fora da zona autorizada -> bloqueante
- introdução de débito técnico não declarado -> falha ou waiver obrigatório

### Saída
`architecture-guard-report.json` com:
- resultado
- desvio
- severidade
- área afetada
- ação obrigatória

## 3. Drift Detector
### Objetivo
Medir desalinhamento entre intenção, contratos e execução.

### Camadas de drift
- intake x PRD
- PRD x SPEC
- SPEC x sprint plan
- sprint plan x execução
- execução x avaliação
- avaliação x release readiness

### Severidades
- `low`: desalinhamento menor, não muda objetivo
- `medium`: desalinhamento exige correção antes de fechar sprint
- `high`: desalinhamento compromete validação
- `critical`: desalinhamento invalida plano atual

### Situações típicas
- PRD promete algo que a SPEC não cobre
- SPEC autoriza módulos diferentes dos realmente alterados
- sprint plan omite evidência exigida na avaliação
- documentação final não representa o que foi executado

### Saída
`drift-report.json` com:
- layer
- finding
- severity
- suspected_root_cause
- remediation

