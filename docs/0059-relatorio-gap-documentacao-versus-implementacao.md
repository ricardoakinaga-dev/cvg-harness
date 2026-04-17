# 0059 - Relatorio de gap entre documentacao e implementacao

## Objetivo

Comparar a trilha documental de `docs/0001` a `docs/0058` com o que esta efetivamente construido no repositório hoje, destacando:
- o que esta implementado de fato
- o que a documentacao descreve com precisao
- o que ainda sobra como gap real
- uma nota de `0-100` por item/area

## Metodo

Base da avaliacao:
- leitura da documentacao numerada em `docs/`
- inspecao do codigo em `src/cvg_harness/`
- checagem da cobertura de testes
- validacao atual da suite

Validacao observada nesta rodada:
- `pytest -q` -> `253 passed`

## Leitura executiva

O estado real do projeto esta muito proximo da trilha documental mais recente.

Resumo direto:
- a base fundacional esta concluida
- o fluxo operacional principal esta concluido
- o runtime/CI opt-in e seus sidecars canônicos estao implementados
- o suporte a provider, contexto resolvido, atalhos de CLI e observabilidade agregada tambem estao implementados
- o maior gap remanescente nao e mais de arquitetura principal, e sim de integracao externa real com executores/provedores fora do harness

Em outras palavras:
- a documentacao nao esta “fantasiando” o sistema
- a maior parte do que ela descreve recente existe no codigo
- o que falta e profundidade externa, nao o esqueleto do produto

## Notas por area

### 1. Fundacao do produto
Nota: `98/100`

Inclui:
- classificacao FAST vs ENTERPRISE
- research
- PRD
- SPEC
- contratos de artefatos
- gates basicos

Gap real:
- baixo
- os docs antigos ainda mostram o amadurecimento historico, mas o codigo atual ja fechou essa base

Evidencia:
- `src/cvg_harness/classification/`
- `src/cvg_harness/research/`
- `src/cvg_harness/prd/`
- `src/cvg_harness/spec_builder/`
- `src/cvg_harness/contracts/`

### 2. Planejamento, lint, guardian e drift
Nota: `96/100`

Inclui:
- `Spec Linter`
- `Architecture Guardian`
- `Drift Detector`
- `Sprint Planner`

Gap real:
- heuristica residual em casos limites ainda existe
- a base esta forte, mas nao ha prova de cobertura total para todas as variacoes humanas possiveis

Evidencia:
- `src/cvg_harness/linter/spec_linter.py`
- `src/cvg_harness/guardian/architecture_guardian.py`
- `src/cvg_harness/drift/drift_detector.py`
- `src/cvg_harness/flow.py`

### 3. Fluxo operacional e gates
Nota: `97/100`

Inclui:
- `progress.json`
- `event-log.jsonl`
- gates do fluxo
- fallback e replan formal
- retomada do ciclo

Gap real:
- praticamente nenhum no nivel canônico
- o que ainda existe e mais refinamento de leitura do que falta estrutural

Evidencia:
- `src/cvg_harness/ledger/`
- `src/cvg_harness/gates/`
- `src/cvg_harness/replan/`
- `src/cvg_harness/flow.py`

### 4. Evaluator e evidencias
Nota: `95/100`

Inclui:
- evidencias estruturadas
- evidencias externas canonicas
- `evaluation-report.json`
- contagem e resumo de evidencia

Gap real:
- o evaluator ainda depende de sinais de entrada que podem ser sintéticos em demos
- em cenarios negativos e de excecao, ainda ha espaco para ficar mais forte

Evidencia:
- `src/cvg_harness/evaluator/`
- `src/cvg_harness/operator/service.py`
- `tests/test_evaluator.py`

### 5. Release readiness e metrics
Nota: `97/100`

Inclui:
- `release-readiness-report.json`
- `delivery-metrics.json`
- pass rate, lead time, rounds, retrabalho, custos
- quebra de sinais externos

Gap real:
- metrics ainda sao principalmente agregacao operacional, nao uma camada analitica profunda de produto

Evidencia:
- `src/cvg_harness/release/release_readiness.py`
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `src/cvg_harness/metrics/metrics_catalog.py`

### 6. Dashboard e observabilidade
Nota: `96/100`

Inclui:
- `dashboard.json`
- quebra por `provider`
- leitura de gates, eventos e metrics

Gap real:
- o dashboard existe e agrega bem, mas a experiencia visual ainda e mais canônica do que exploratoria

Evidencia:
- `src/cvg_harness/dashboard/dashboards.py`
- `tests/test_agents_extended.py`

### 7. Runtime opt-in e sidecars
Nota: `96/100`

Inclui:
- `runtime-hooks.json`
- `external-evidence-manifest.json`
- `ci-result.json`
- eventos canônicos de runtime e CI

Gap real:
- a maior parte do caminho esta implementada, mas a execucao real continua opt-in e limitada ao que o harness permite

Evidencia:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/auto_runtime/runtime_automation.py`
- `src/cvg_harness/contracts/artifact_contracts.py`

### 8. Providers, contexto resolvido e UX de runtime/CI
Nota: `95/100`

Inclui:
- `provider` nos sidecars
- `required_context`
- `example_contexts`
- `raw_context` e `resolved_context`
- resolucao de contexto para `github-actions`, `gitlab-ci` e `azure-pipelines`
- atalhos de CLI para `repository`, `ci-run-id`, `ci-api`, `ci-url`, `ci-status`

Gap real:
- ainda e uma UX de operador com foco em contexto e comandos, nao uma integracao real completa com cada provider
- os providers existem como perfis e resolucoes; o dispatch externo real continua pouco acoplado a servicos externos de verdade

Evidencia:
- `src/cvg_harness/auto_runtime/runtime_automation.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/operator/service.py`
- `tests/test_runtime.py`
- `tests/test_operator_cli.py`

### 9. Executor externo
Nota: `74/100`

Inclui:
- `ExternalExecutorAdapter`
- `ExternalExecutorBridge`
- planejamento e dispatch opt-in
- adaptadores `manual-review` e `local-cli`

Gap real:
- nao existe ainda uma integracao ampla e real com executores externos concretos fora do exemplo local/manual
- a caminha esta pronta, mas o ecossistema de adapters reais ainda e pequeno

Evidencia:
- `src/cvg_harness/auto_runtime/external_executor.py`
- `docs/0047-sprint-19-executor-externo-e-evidencia-operacional.md`

### 10. Documentacao e continuidade
Nota: `93/100`

Inclui:
- trilha numerada
- historico preservado
- docs recentes coerentes com o codigo
- memoria de continuidade atualizada

Gap real:
- alguns docs historicos ainda descrevem estagios anteriores e usam numeros de validacao antigos por design
- isso nao e erro funcional; e um historico preservado

Evidencia:
- `docs/0056-sprint-28-validacao-de-contexto-runtime-ci.md`
- `docs/0057-sprint-29-contexto-executavel-por-provider.md`
- `docs/0058-sprint-30-atalhos-operacionais-para-runtime-ci.md`
- `docs/0058-sprint-30-observabilidade-de-provider.md`

## Notas por sprint/iteracao recente

### Sprint 19 a 24
Nota media: `94/100`

Status:
- executor externo, evidencias e CI canonico estao bem amarrados
- os sidecars operacionais estao implementados

Gap principal:
- a execucao externa ainda esta mais forte como contrato e orquestracao do que como integraçao real ampla

### Sprint 25 a 28
Nota media: `96/100`

Status:
- ingestao real de `ci_result`
- URL remota
- perfis runtime/CI com contexto operacional
- validacao explicita de compatibilidade

Gap principal:
- ainda existia um catalogo de perfis mais descritivo do que executavel em alguns casos

### Sprint 29 a 30
Nota media: `95/100`

Status:
- contexto executavel por provider
- atalhos operacionais de CLI
- provider agregado em metrics e dashboard

Gap principal:
- provider real ainda e perfil/contexto, nao uma integracao completa com providers externos de producao

## Nota global

`94/100`

## Leitura final do gap

O gap mais importante hoje nao esta em:
- planning
- contracts
- gates
- flow orchestration
- runtime sidecars
- provider context
- metrics
- dashboard

O gap principal esta em:
- integracao externa real mais ampla para executores e providers
- ampliacao do ecossistema de adapters fora do harness
- profundidade analitica adicional em cenarios de excecao e evidencias negativas

## Conclusao

Se a pergunta e “o que a documentacao promete versus o que o codigo realmente entrega?”, a resposta e:

- a documentacao recente esta bastante aderente ao build atual
- os itens mais novos das Sprints 28 a 30 estao, em grande parte, implementados
- o principal delta restante e evolucao externa real, nao estrutura interna

