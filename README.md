# CVG Harness

CLI-first operational orchestrator para demanda de software no terminal.

O `cvg-harness` preserva uma engine interna de governança com classificação, planning, gates, guard, evaluator, drift, readiness, ledger e métricas. A experiência principal agora é de operação canônica no terminal: iniciar uma demanda, acompanhar estado, aprovar a sprint atual, continuar o ciclo e decidir quando replanejar.

## Instalação

```bash
pip install -e .
```

## Modo Operador

A entrada principal do produto é:

```bash
cvg run "criar módulo de permissões por setor"
```

Esse comando:
- cria uma run operacional em `.cvg-harness/runs/<run_id>/`
- classifica a demanda (`FAST` ou `ENTERPRISE`)
- executa `research`, `prd`, `spec`, `spec lint` e `sprint plan`
- persiste `flow-state.json`, `progress.json` e `event-log.jsonl`
- deixa a run pronta para execução controlada, aguardando decisão humana

Fluxo canônico de uso:

```bash
# 1. Iniciar demanda
cvg run "criar módulo de permissões por setor"

# 2. Ver estado atual
cvg status
cvg inspect

# 3. Aprovar a sprint atual para começar a execução controlada
cvg approve

# 4. Informar arquivos tocados e continuar o ciclo
cvg continue --changed-file src/auth/login.py

# 5. Informar evidências para avaliação/release
cvg continue \
  --changed-file src/auth/login.py \
  --evidence "implementação do módulo auth" \
  --evidence "testes unitários" \
  --evidence "logs de execução"

# 5b. Ou usar evidência estruturada
cvg continue \
  --changed-file src/auth/login.py \
  --evidence-file evidence.json

# 6. Inspecionar trilha operacional
cvg events
cvg metrics

# 7. Rodar hooks/runtime opt-in com perfil conhecido
cvg runtime --event ci_result --profile github-actions \
  --repository openai/cvg-harness \
  --ci-run-id 77 \
  --ci-url https://github.com/openai/cvg-harness/actions/runs/77 \
  --ci-status passed

# 8. Preparar dispatch externo com contexto provider-aware
cvg dispatch --executor manual-review \
  --repository openai/cvg-harness \
  --ci-run-id 77 \
  --ci-url https://github.com/openai/cvg-harness/actions/runs/77 \
  --ci-status passed

# 9. Rodar runtime com provider alternativo
cvg runtime --event ci_result --profile azure-pipelines \
  --ci-url https://dev.azure.com/openai/cvg-harness/_build/results?buildId=42 \
  --ci-status passed
```

### Comandos canônicos

- `cvg run "demanda"`: inicia a run, gera planning e prepara a sprint atual.
- `cvg status`: mostra projeto, run, modo, fase, gate, sprint atual, bloqueios e próximo passo.
- `cvg inspect [SPRINT-001]`: mostra artefatos, relatórios, timeline causal, evidência, blockers e decisões da sprint atual ou informada.
- `cvg continue`: retoma a run no último estado válido; aceita `--changed-file`, `--evidence`, `--evidence-json` e `--evidence-file`.
- `cvg pause`: pausa a run atual sem destruir estado.
- `cvg approve [SPRINT-001]`: aprova a sprint atual para execução controlada.
- `cvg replan --reason "..."`: registra replanejamento formal.
- `cvg events`: mostra eventos recentes do `event-log.jsonl` da run atual.
- `cvg metrics`: mostra métricas operacionais da run atual.
- `cvg runtime-profiles`: lista os perfis conhecidos de runtime/CI, com `provider`, `required_context`, `example_contexts` e `command_examples`.
- `cvg dispatch`: prepara handoff explícito para executor externo e aceita os mesmos atalhos provider-aware do runtime.

### O que o harness faz sozinho

- planning e governança até a sprint pronta para execução
- persistência de estado e artefatos
- validação arquitetural (`guard`)
- avaliação de evidência (`evaluator`)
- detecção de drift
- decisão de release readiness

### Onde ele para e exige operador

- aprovação explícita da sprint atual (`cvg approve`)
- fornecimento de `changed_files` e evidências reais para seguir o ciclo
- decisão de replanejar, corrigir ou continuar quando houver bloqueio
- execução real de comandos externos quando hooks/runtime forem usados

## Workspace Operacional

Estrutura canônica criada por `cvg run`:

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
        classification.json
        research-notes.{json,md}
        system-map.{json,md}
        prd.{json,md}
        spec.{json,md}
        sprint-plan.json
        execution-order.json
        handoff-*.json
      reports/
        spec-lint-report.json
        evaluation-report.json
        drift-report.json
        release-readiness-report.json
        gates/
          gate-GATE_0.json
          ...
          gate-GATE_9.json
      event-log.jsonl
      flow-state.json
      progress.json
      run.json
      delivery-metrics.json
      artifacts/execution-input.json
      artifacts/evidence-manifest.json
```

Isso permite retomada (`cvg continue`), inspeção (`cvg inspect`) e auditoria (`cvg events`).

## Modo Avançado / Engineering Tools

Os comandos granulares continuam disponíveis para uso técnico e automação de baixo nível:

```bash
cvg classify --project x --demand "y" --dimensions '{"impacto_arquitetural":1}' --rationale "z"
cvg lint --spec spec.json --mode ENTERPRISE
cvg guard --files "src/a.py" --authorized '["src/a"]' --prohibited '["src/legacy"]'
cvg drift --intake intake.json --prd prd.json --spec spec.json
cvg progress new --project x --feature y --mode FAST
cvg progress update --input progress.json --output progress.json --gate GATE_0=approved
cvg event --log event-log.jsonl --add "sprint_approved|evaluator|sprint-1"
cvg handoff --source prd.md --target "Spec Builder" --objective "gerar spec"
cvg template --type spec --data '{}'
```

Esses comandos preservam a engine como toolkit técnico, mas não são mais a experiência principal do produto.

## Loop Operacional

```text
Demanda
  -> run
  -> classification
  -> research
  -> prd
  -> spec
  -> spec lint
  -> sprint plan
  -> approve
  -> continue (changed_files)
  -> guard
  -> continue (evidence)
  -> evaluator
  -> drift
  -> release readiness
  -> conclude | block | replan
```

## Runtime e Executor

O `cvg-harness` é o orquestrador. Ele não assume, por padrão, que será o executor final da mudança.

- o `RuntimeExecutor` existe e pode rodar hooks reais
- o contrato `ExternalExecutorAdapter` formaliza integração com executores externos
- execução real é `opt-in`
- integração com agentes externos continua separada do harness
- o modo padrão continua seguro para demonstração e validação determinística
- métricas e dashboard já agregam `runtime_provider_breakdown`

Em outras palavras: o harness governa, registra e decide; a execução externa continua separável.

Preferências de handoff externo agora também podem ser ajustadas por projeto em `.cvg-harness/adapter-policy.json`, sem remover os defaults do produto. Isso permite priorizar ou desabilitar adapters por `capability` mantendo a escolha final explícita e auditável em `external-dispatch-plan.json`.

## Arquitetura Preservada

A engine interna continua no centro do produto:

- `classification/`: FAST vs ENTERPRISE
- `research/`: pesquisa e system map
- `prd/`: definição de problema, objetivo e escopo
- `spec_builder/`: SPEC executável
- `linter/`: Spec Linter
- `sprint/`: Sprint Planner
- `guardian/`: Architecture Guardian
- `evaluator/`: QA / evidência
- `drift/`: Drift Detector
- `release/`: Release Readiness
- `ledger/`: progress ledger + event log
- `metrics_agg/`: métricas operacionais
- `flow.py`: `FlowOrchestrator`
- `operator/`: camada de UX operacional sobre a engine
- `cli/`: CLI canônica + comandos avançados

## Exemplos

```bash
python3 examples/demo_complete_flow.py
python3 examples/example_flow.py
python3 examples/example_research_prd_spec.py
python3 examples/example_evaluator_release.py
python3 examples/example_fallback_demo.py
```

O demo principal continua usando o `FlowOrchestrator` real. Alguns exemplos didáticos usam evidências sintéticas ou descritivas para demonstrar o ciclo sem depender de executor externo real.

## Validação

```bash
pytest -q
python3 examples/demo_complete_flow.py
cvg --help
```

## Estado Atual

- modo operador canônico no terminal
- modo avançado preservado
- artefatos, gates e rastreabilidade mantidos
- release canônico persistido em `release-readiness-report.json`
- `release-readiness.md` permanece apenas como sidecar opcional para leitura humana
