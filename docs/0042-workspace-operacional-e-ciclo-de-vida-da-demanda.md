# 0042 - Workspace operacional e ciclo de vida da demanda

## Objetivo

Documentar a estrutura de workspace usada pelo modo operador e explicar como uma demanda nasce, persiste, é retomada e se encerra.

## Estrutura de workspace

Raiz operacional:

```text
.cvg-harness/
  current-run.txt
  run-index.json
  artifacts/
  ledgers/
  logs/
  reports/
  runs/
    <run_id>/
      artifacts/
      reports/
      event-log.jsonl
      flow-state.json
      progress.json
      run.json
      artifacts/external-dispatch-plan.json
      delivery-metrics.json
      artifacts/execution-input.json
      artifacts/evidence-manifest.json
```

## Papel de cada elemento

### `current-run.txt`
Aponta para a run corrente usada por `status`, `inspect`, `continue`, `pause`, `approve`, `replan`, `events` e `metrics`.

### `run-index.json`
Índice resumido das runs conhecidas no workspace.

### `runs/<run_id>/run.json`
Registro operacional da run no modo operador.

Campos principais:
- `run_id`
- `project`
- `demand`
- `workspace_root`
- `run_workspace`
- `mode`
- `operator_status`
- `next_action`
- `pending_human_action`
- `current_phase`
- `current_gate`
- `current_sprint`
- `summary`

### `flow-state.json`
Estado do `FlowOrchestrator`.

### `progress.json`
Ledger de progresso com gates, bloqueios e status.

### `event-log.jsonl`
Trilha cronológica de eventos operacionais.

### `artifacts/`
Artefatos canônicos produzidos durante a run.

### `reports/`
Relatórios e resultados de validação.

## Criação de uma run

`cvg run`:
- cria o diretório da run
- executa planning inicial
- persiste estado inicial
- registra estado mínimo de run (sem dispatch automático)
- atualiza `current-run.txt`
- atualiza `run-index.json`

## Ciclo de vida da demanda

### 1. Nascimento
A demanda entra por `cvg run "..."`.

### 2. Planejamento
A engine produz classificação, research, PRD, SPEC, lint e sprint plan.

### 3. Espera de decisão humana
A run fica em `waiting_input`, normalmente com `pending_human_action=approve_sprint`.

### 4. Execução controlada
Após `cvg approve`, o operador fornece:
- arquivos alterados
- evidências textuais ou estruturadas

### 5. Validação formal
O sistema roda:
- `Architecture Guardian`
- `Evaluator`
- `Drift Detector`
- `Release Readiness`

### 6. Encerramento
A run termina como:
- `completed`
- `blocked`
- `paused`

## Retomada

A retomada é feita com:

```bash
cvg continue
```

ou, mais realisticamente:

```bash
cvg continue --changed-file ... --evidence ...
```

A retomada usa o último estado persistido e não depende de memória de sessão.

## Pausa

`cvg pause`:
- não apaga artefatos
- não apaga estado
- apenas altera o status operacional da run

## Replanejamento

`cvg replan --reason "..."`:
- registra decisão formal
- persiste artefato de replanejamento
- muda a run para um estado que exige revisão humana

## Encerramento e outputs finais

Quando a run conclui com sucesso, o operador deve conseguir inspecionar:
- gates persistidos
- decisão de readiness
- métricas
- event log
- estado final sincronizado entre `run.json`, `flow-state.json` e `progress.json`

## Regra de projeto

O workspace operacional precisa continuar:
- claro para inspeção humana
- consistente para retomada
- suficiente para auditoria
- separado do código do projeto sem esconder a relação com ele
