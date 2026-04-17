# 0039 - Operação real do CVG Harness

## Objetivo

Definir como o `cvg-harness` deve ser usado no dia a dia como orquestrador operacional no terminal.

A intenção deste documento não é descrever a engine inteira, e sim o fluxo canônico de operação para quem está conduzindo uma demanda do início ao fim.

## Entrada principal

A entrada canônica do produto é:

```bash
cvg run "descrição da demanda"
```

Exemplo:

```bash
cvg run "criar módulo de permissões por setor"
```

Esse comando cria uma run operacional e executa automaticamente:

1. classificação da demanda
2. research
3. PRD
4. SPEC
5. spec lint
6. sprint planning
7. preparação do estado para execução controlada

Ao final desse primeiro passo, a run fica pronta para inspeção e aprovação humana.

## Loop operacional real

O loop canônico atual do produto é:

```text
receber demanda
  -> classificar
  -> pesquisar
  -> gerar PRD
  -> gerar SPEC
  -> validar SPEC
  -> gerar sprint plan
  -> aguardar aprovação humana
  -> validar changed_files
  -> avaliar evidências
  -> detectar drift
  -> decidir readiness
  -> concluir | bloquear | replanejar
```

Esse loop já existe no código. Ele não depende só de documentação.

## Fluxo diário do operador

### 1. Iniciar a run

```bash
cvg run "criar módulo de permissões por setor"
```

Saída esperada:
- `run_id`
- projeto
- modo (`FAST` ou `ENTERPRISE`)
- workspace da run
- fase atual
- gate atual
- próximo passo

### 2. Ver estado atual

```bash
cvg status
```

Mostra:
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
- resumo da run

### 3. Inspecionar artefatos e sprint

```bash
cvg inspect
cvg inspect SPRINT-001
```

Mostra:
- artefatos gerados
- relatórios disponíveis
- sprints planejadas
- detalhes da sprint alvo
- avaliação já realizada, quando existir
- timeline causal de decisões, blockers e evidências

### 4. Aprovar sprint atual

```bash
cvg approve
```

O produto não entra em execução controlada sem aprovação humana explícita.

### 5. Continuar a run

Caminho mínimo:

```bash
cvg continue --changed-file src/auth/login.py
```

Depois, quando houver evidência:

```bash
cvg continue \
  --changed-file src/auth/login.py \
  --evidence "implementação do módulo auth" \
  --evidence "testes unitários" \
  --evidence "logs de execução"

Ou com evidência estruturada:

```bash
cvg continue \
  --changed-file src/auth/login.py \
  --evidence-file evidence.json
```
```

No estado atual, `continue` pode:
- rodar `Architecture Guardian`
- aguardar evidências
- rodar `Evaluator`
- rodar `Drift Detector`
- rodar `Release Readiness`
- concluir a run
- bloquear a run

### 6. Pausar ou replanejar

```bash
cvg pause
cvg replan --reason "scope-violated-guard"
```

## Papel humano

O operador continua no centro das decisões críticas.

O harness faz:
- planning
- persistência de estado
- validação formal
- avaliação de evidência
- detecção de desalinhamento
- decisão de readiness

O operador decide:
- se aprova a sprint atual
- quando há mudança suficiente para continuar
- quais evidências são apresentadas
- quando replanejar
- quando interromper a run

## Critérios de parada

A run pode encerrar em três estados relevantes:

### Concluída
- `Release Readiness = APPROVED`
- `flow-state.json` em `completed`
- `progress.json` sincronizado

### Bloqueada
- guard, evaluator, drift ou release impediram promoção
- o próximo passo esperado é inspeção e eventual `replan`

### Pausada
- interrupção voluntária do operador
- retomada via `cvg continue`

## Outputs finais relevantes

Outputs operacionais principais:
- `classification.json`
- `research-notes.{json,md}`
- `system-map.{json,md}`
- `prd.{json,md}`
- `spec.{json,md}`
- `sprint-plan.json`
- `execution-order.json`
- `event-log.jsonl`
- `flow-state.json`
- `progress.json`
- `reports/gates/gate-GATE_*.json`
- `release-readiness-report.json`
- `delivery-metrics.json`

## O que este produto não promete

O `cvg-harness` não promete:
- execução automática irrestrita de código em produção
- substituição do executor final por padrão
- automação cega sem checkpoints humanos
- interface web como experiência principal

A proposta atual é terminal-first, governada e auditável.
