# 0040 - Design do CLI e contratos de comando

## Objetivo

Definir a camada canônica de CLI do `cvg-harness`, separando comandos de operação de demanda dos comandos granulares de engenharia.

## Princípio central

A CLI possui dois níveis formais:

1. modo operador
2. modo técnico / avançado

A engine interna é a mesma. O que muda é a experiência de entrada e o nível de abstração exposto.

## 1. Modo operador

Esses são os comandos que devem aparecer primeiro no `cvg --help`.

### `cvg run "demanda"`

Contrato de entrada:
- `demanda`: texto livre obrigatório
- `--project`: opcional
- `--mode {AUTO,FAST,ENTERPRISE}`: opcional
- `--workspace`: opcional

Contrato de saída:
- cria `.cvg-harness/`
- cria uma nova run em `.cvg-harness/runs/<run_id>/`
- gera planning inicial e estado persistido
- imprime resumo operacional da run

Erros possíveis:
- falha de escrita no workspace
- falha em alguma etapa do planning inicial

### `cvg status`

Entrada:
- `--workspace`: opcional
- `--json`: opcional

Saída:
- projeto
- demanda
- run atual
- modo
- status do operador
- fase atual
- gate atual
- sprint atual
- bloqueios
- próximo passo
- resumo

### `cvg inspect [SPRINT-001]`

Entrada:
- `target`: opcional, normalmente sprint id
- `--json`: opcional
- `--workspace`: opcional

Saída:
- dados da run atual
- artefatos disponíveis
- relatórios disponíveis
- lista de sprints ou detalhes da sprint alvo
- avaliação, quando existir
- resumo causal com blockers, changed_files, evidências e decisões

### `cvg continue`

Entrada:
- `--changed-file PATH` repetível
- `--evidence TEXTO` repetível
- `--evidence-json JSON` repetível
- `--evidence-file ARQUIVO_JSON`
- `--round N`
- `--json`
- `--workspace`

Saída:
- resumo da continuação da run
- artefato `execution-input.json`
- artefato `evidence-manifest.json`, quando houver evidência
- relatório de `guard`, quando houver
- relatório de `evaluation`, quando houver
- relatório de `drift`, quando houver
- relatório de `release`, quando houver
- estado atualizado da run

Comportamento atual:
- sem aprovação prévia: erro
- com `changed_files`: roda `guard`
- com evidências: roda `evaluation`, `drift` e `release`

### `cvg pause`

Saída:
- marca a run atual como pausada
- próximo passo esperado passa a ser `cvg continue`

### `cvg approve [SPRINT-001]`

Saída:
- marca a sprint atual como aprovada para execução controlada
- muda a pendência humana para fornecimento de inputs de execução

### `cvg replan --reason "..."`

Saída:
- registra decisão formal de replanejamento
- persiste `replan-decision.json`
- emite evento operacional correspondente

### `cvg events`

Entrada:
- `--limit`
- `--type`
- `--json`

Saída:
- eventos mais recentes da run atual
- por padrão, leitura do `event-log.jsonl` da run

### `cvg metrics`

Saída:
- `lead_time`
- `rounds`
- `pass_rate`
- `custo`
- `falhas_por_tipo`

## 2. Modo técnico / avançado

Comandos preservados:
- `classify`
- `lint`
- `guard`
- `drift`
- `progress`
- `event`
- `handoff`
- `template`

Esses comandos continuam acessíveis porque a engine interna também precisa operar como toolkit técnico e superfície de automação.

## Relação entre comandos e artefatos

### `run`
Produz principalmente:
- `classification.json`
- `research-notes.{json,md}`
- `system-map.{json,md}`
- `prd.{json,md}`
- `spec.{json,md}`
- `sprint-plan.json`
- `execution-order.json`
- `progress.json`
- `flow-state.json`
- `event-log.jsonl`

### `continue`
Pode produzir:
- `guard` no estado do fluxo
- `evaluation-report.json`
- `drift-report.json`
- `release-readiness-report.json`
- gates adicionais em `reports/gates/`

### `events`
Consome:
- `event-log.jsonl`

### `metrics`
Consome e/ou gera:
- `delivery-metrics.json`
- `event-log.jsonl`
- `progress.json`

## Estados esperados no modo operador

Estados principais hoje:
- `waiting_input`
- `active`
- `paused`
- `blocked`
- `completed`

Pendências humanas típicas:
- `approve_sprint`
- `provide_execution_inputs`
- `provide_evidence`
- `review_blocker`
- `review_replan`
- `resume_run`

## Erros operacionais esperados

Casos já tratados pela CLI:
- continuar sem aprovação prévia
- aprovar sprint diferente da sprint atual
- usar workspace sem `current-run.txt`
- ler artefatos inexistentes
- JSON malformado nos comandos avançados

## Princípios de UX

- operador vê primeiro o fluxo canônico
- engineering tools continuam acessíveis, mas não são a entrada principal
- a CLI deve sempre deixar claro o próximo passo
- a CLI não promete automação irrestrita que o código não sustenta
