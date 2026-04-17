# Contributing to CVG Harness

## Setup

```bash
# Clone e instalação em modo desenvolvimento
pip install -e ".[dev]"

# Executar testes
pytest tests/ -v

# Executar demo
python examples/demo_complete_flow.py
```

## Estrutura

```
src/cvg_harness/
├── classification/     # P0 - Classificador FAST vs ENTERPRISE
├── contracts/         # P0 - Contratos de artefatos e handoff
├── gates/            # P0 - Gates e política de aprovação
├── fallback/         # P0 - Política de fallback e replanejamento
├── linter/           # P0 - Spec Linter
├── guardian/         # P0 - Architecture Guardian
├── drift/            # P0 - Drift Detector
├── ledger/           # P1 - Progress Ledger e Event Log
├── metrics/          # P1 - Catálogo de métricas
├── templates/        # P1 - Templates revisados
├── dashboard/        # P2 - Dashboards
├── agent_scoring/    # P2 - Scoring por agente
├── sprint_history/   # P2 - Histórico comparativo de sprints
├── patterns/         # P2 - Biblioteca de padrões reutilizáveis
├── orchestration/    # P3 - Orquestração multi-projeto
├── domain_optimization/  # P3 - Otimização por domínio
├── comparative_intelligence/  # P3 - Inteligência comparativa
├── auto_runtime/     # P3 - Automação de runtime
├── flow.py           # Flow Orchestrator
├── repl.py           # REPL interativo
└── cli/              # CLI
```

## Regras

### P0 (Crítico)
Qualquer PR que afete módulos P0 deve incluir:
- Testes unitários cobrindo as regras principais
- Atualização do CHANGELOG.md

### Convenções de código
- dataclasses para estruturas de dados
- Tipos explícitos em funções públicas
- Nome de arquivo: `snake_case.py`
- Nome de classe: `PascalCase`
- Funções e variáveis: `snake_case`

### Commit
```
<tipo>(<módulo>): <descrição>

Tipos: feat, fix, docs, test, refactor
Exemplo: feat(classifier): adicionar suporte a override
```

## Testes

```bash
# Todos os testes
pytest tests/ -v

# Com coverage
pytest tests/ --cov=cvg_harness --cov-report=term-missing

# Apenas integração
pytest tests/test_integration.py -v

# Um módulo específico
pytest tests/test_classifier.py -v
```

## CI/CD

O projeto não possui CI configurado ainda. Quando configurar:
- Todos os testes devem passar
- Lint/format check obrigatório
- Type check com mypy
