# 0038. Nota exploratória - Dashboard canônico e contrato de visualização

## Objetivo
Registro exploratório de uma visualização operacional do `Dashboard` como artefato derivado de `progress.json`, `event-log.jsonl` e `delivery-metrics.json`.

Nota:
- este documento não faz parte da trilha oficial ativa;
- o ciclo oficial segue em `docs/0038-sprint-16-endurecimento-guardian-drift.md`.

## Estado de partida
- O projeto continua aprovado e o fluxo fim a fim permanece estável.
- `delivery-metrics.json` já passou a existir como saída canônica da Sprint 15.
- O módulo `src/cvg_harness/dashboard/dashboards.py` já monta uma visão operacional a partir de `progress` e `event log`.
- Ainda falta contrato explícito para `dashboard.json` e cobertura de regressão que prove persistência/leitura da visão sem inventar campos fora do estado real.

## Foco da nota
Conter a proposta em um sidecar operacional, sem tratar isso como sprint ativa.

## Itens do sprint

### 1. Definir contrato canônico para `dashboard.json`
**Status:** `done`

Objetivo:
- registrar o dashboard como artefato formal, com campos estáveis e derivação clara a partir do estado real.

Arquivos alvo:
- `src/cvg_harness/dashboard/dashboards.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `docs/0006-agentes-e-responsabilidades.md`

Mudanças esperadas:
- adicionar contrato explícito para `dashboard.json`;
- manter `DashboardData` alinhado ao contrato;
- deixar claro que o dashboard é uma visão operacional derivada, não uma nova fonte de verdade.

Critérios de saída:
- `dashboard.json` passa a ter contrato formal e validável;
- os campos esperados saem do estado real sem aliases implícitos;
- a documentação distingue contrato canônico de leitura humana.

### 2. Cobrir build/save/load do dashboard com dados reais
**Status:** `done`

Objetivo:
- provar que a visão do dashboard nasce do workspace real e pode ser persistida sem perda de coerência.

Arquivos alvo:
- `tests/test_agents_extended.py`
- `tests/test_integration.py`
- `src/cvg_harness/dashboard/dashboards.py`

Mudanças esperadas:
- adicionar teste de construção do dashboard a partir de `progress.json` e `event-log.jsonl`;
- validar persistência e recarga do artefato;
- checar coerência com métricas e blocos observados no workspace.

Critérios de saída:
- o dashboard é reprodutível a partir de artefatos vivos;
- o teste protege contra regressão de shape ou origem dos dados.

### 3. Ajustar a trilha documental do P2 para refletir o dashboard como sidecar operacional
**Status:** `done`

Objetivo:
- alinhar a trilha de documentação para que `dashboard` apareça como evolução incremental da observabilidade, sem exagerar seu papel.

Arquivos alvo:
- `docs/0014-backlog-priorizado.md`
- `docs/0016-backlog-executavel-de-correcao.md`
- `README.md`

Mudanças esperadas:
- registrar o dashboard como visão operacional derivada;
- manter a prioridade P2 coerente com o estado atual dos contratos;
- evitar que a documentação sugira novo sistema de decisão.

Critérios de saída:
- a leitura rápida deixa claro que o dashboard é sidecar operacional;
- a trilha aponta para o próximo ciclo sem reabrir o núcleo aprovado.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "dashboard.json|DashboardData|save_dashboard|load_dashboard|dashboard" src docs tests README.md -g '!**/__pycache__/**'
```

## Critério de encerramento
- `dashboard.json` tem contrato formal e testado;
- o dashboard persiste leitura operacional sem inventar estado;
- a trilha documental deixa o papel do dashboard explícito como visão derivada;
- o escopo permanece pequeno e não mexe no comportamento aprovado do fluxo.

### Validação executada
- Completa: `pytest -q` -> `190/190`.
- Demo: `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`.

## Encadeamento
- Sprint anterior: `docs/0036-sprint-15-metricas-operacionais-canônicas.md`.
