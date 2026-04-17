# 0047 — Operação no Workspace e Ciclo Completo da Demanda

## Workspace-aware por padrão

Ao iniciar `harness` no diretório atual:

- `WorkspaceManager` resolve `Path.cwd()`
- cria (se necessário) `.harness/`
- inicializa subpastas de persistência:
  - `runs/`
  - `artifacts/`
  - `reports/`
  - `logs/`
  - `ledgers/`
  - `session/`

Implementação: [`WorkspaceManager`]( /home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/workspace/manager.py ).

## Estrutura de ciclo de demanda

### 1) Nova demanda

Input: `> criar módulo de permissões por setor`

- `FrontAgent._new_demand` infere intenção com `infer_dimensions_from_demand`.
- `calculate_mode` retorna `FAST` ou `ENTERPRISE`.
- cria run via `OperatorService.start_run`.
- atualiza estado de sessão (`session/current.json`) com `run_id`.

### 2) Execução da engine

O motor interno executa:

- classificação
- research
- PRD
- SPEC + lint
- planner de sprints
- guard/architecture guard
- drift detect
- evaluator
- release readiness
- metrics + ledger + event-log

### 3) Interações durante execução

- `status`: visão resumida do fluxo e próximo passo
- `inspect`: artefatos, evidências e decisões conhecidas
- `continue`: avança com evidência e arquivos opcionais
- `replaneje ...`: dispara replanejamento
- `resumo`: quando for necessário validar entrega

### 4) Conclusão

- `summary` ou fechamento automático do operador retornam:
  - `run_id`, `status`, `fase/gate`
  - `sprints` executadas
  - decisão de evaluator/release/guardian/drift
  - artefatos e evidências persistidas

## Retomada

Formas de retomada:

- `harness resume`
- `> retome`

Ambas carregam a run ativa de:

- `.harness/current-run.txt` e
- `.harness/session/current.json`.

Após recuperar run, o agente imprime pendência e próximo passo.
