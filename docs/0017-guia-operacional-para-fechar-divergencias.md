# 0017. Guia operacional para fechar divergências

## Objetivo
Este documento existe para o executor que não está conseguindo inferir sozinho o que está divergente.

O papel desta doc é transformar a auditoria em procedimento operacional:
- o que está divergente hoje
- como detectar cada divergência
- em que ordem corrigir
- quais arquivos editar
- como validar cada correção
- quando parar e não avançar para a próxima etapa

Use este documento junto com `docs/0016-backlog-executavel-de-correcao.md`.

`0016` é o quadro de status.
`0017` é o manual de execução.

Observação: esta trilha descreve a situação histórica de divergência; o estado atual já está consolidado em `docs/0018-sprint-02-checklist-e-patch-plan.md`, `docs/0019-checklist-final-de-aprovacao.md` e `docs/0020-sprint-03-consolidacao-documental.md`.

## Regra de trabalho
- Não atacar `PR-06` ou `PR-07` antes de estabilizar `PR-01` a `PR-05`.
- Não fazer correções “silenciosas” em schema. Se mudar um nome de campo, atualizar produtor, consumidor, contrato e teste na mesma mudança.
- Não deixar adapter temporário sem comentário e sem teste.
- Não considerar “implementado” se só o teste passar mas o contrato documental continuar divergente.
- Ao final de cada bloco, rodar os testes do bloco e uma suíte curta de integração.

## Comando de diagnóstico inicial
Rodar estes comandos antes de começar qualquer correção.

```bash
pytest -q
rg -n "status|state|release-readiness|execution_order|not_executed|orquestração completa|PR-07|pass$|replan_requested|gate-gate_" src README.md examples tests docs -g '!**/__pycache__/**'
```

Se o resultado desses comandos não mudar depois de uma PR, a PR provavelmente não fechou a divergência certa.

## Divergências objetivas já confirmadas

### 1. `GateResult` e `ReleaseReadiness` usam campos incompatíveis
Estado atual:
- `src/cvg_harness/gates/gate_policy.py` usa `GateResult.state`
- `src/cvg_harness/release/release_readiness.py` lê `gate_result.get("status")`

Efeito prático:
- o release engine pode interpretar gate aprovado como `not_started`
- a decisão final de release fica inconsistente com os gates reais

### 2. O orquestrador não gera `execution-order.json`
Estado atual:
- `src/cvg_harness/sprint/sprint_planner.py` calcula `execution_order`
- `src/cvg_harness/flow.py` não persiste isso em `artifacts/execution-order.json`

Efeito prático:
- contrato existe
- artefato prometido não existe
- consumidor externo não consegue seguir a ordem declarada

### 3. O fluxo não avalia nem persiste formalmente `GATE_0` a `GATE_9`
Estado atual:
- existe `evaluate_gate()` em `src/cvg_harness/gates/gate_policy.py`
- `src/cvg_harness/flow.py` muda `current_gate`, mas não executa a política formal em cada etapa
- `check_release_readiness()` tenta ler resultados de gate que o próprio fluxo não gera

Efeito prático:
- há transição de fase, mas não há trilha formal de aprovação por gate
- `release-readiness` consolida dados parciais ou inexistentes

### 4. Ainda existe stub crítico no `ArchitectureGuardian`
Estado atual:
- `src/cvg_harness/guardian/architecture_guardian.py` tem `pass` em `_check_unauthorized_boundary_change`

Efeito prático:
- a regra aparece como implementada, mas não protege nada

### 5. `DriftDetector` ainda não cobre `evaluation x release readiness`
Estado atual:
- `src/cvg_harness/drift/drift_detector.py` cobre até `execucao_x_avaliacao`
- não existe camada `avaliacao_x_release_readiness`

Efeito prático:
- release pode aprovar mesmo se a avaliação anterior estiver desalinhada

### 6. `MetricsAggregator` calcula métricas arbitrárias
Estado atual:
- `lead_time_hours = estimatedCostUsd / 10`
- `retrabalho_hours = total_rounds * 2`

Efeito prático:
- o artefato parece objetivo, mas os números não vêm de eventos reais

### 7. `RuntimeExecutor` continua placeholder
Estado atual:
- `src/cvg_harness/auto_runtime/runtime_automation.py` retorna `status: not_executed`

Efeito prático:
- a integração externa não é usável nem em modo mínimo

### 8. README e examples comunicam mais do que o código realmente faz
Estado atual:
- `README.md` marca `PR-07` como concluído
- `examples/demo_complete_flow.py` ainda injeta estado manualmente em pontos do fluxo

Efeito prático:
- a documentação pública contradiz o estado real do projeto

## Ordem obrigatória de execução
1. PR-01
2. PR-02
3. PR-03
4. PR-04
5. PR-05
6. PR-06
7. PR-07

Se uma etapa quebrar contrato de uma etapa anterior, voltar e corrigir antes de seguir.

## PR-01. Fechar incompatibilidades de schema e contrato

### Objetivo operacional
Deixar produtores, consumidores, contratos e testes usando o mesmo vocabulário.

### Arquivos-alvo
- `src/cvg_harness/gates/gate_policy.py`
- `src/cvg_harness/release/release_readiness.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `src/cvg_harness/types.py`
- `tests/test_pr01_schema_unification.py`
- `tests/test_evaluator.py`

### Passo a passo
1. Escolher o campo canônico do resultado de gate.
Recomendação: manter `GateResult.state`, porque isso já está implementado em `gate_policy.py` e nos testes `test_pr01_*`.

2. Ajustar `ReleaseReadinessEngine.assess()` para consumir `state`, não `status`.
Se necessário, aceitar `status` só como compatibilidade de leitura temporária, mas a saída consolidada deve usar o mesmo nome definido como canônico.

3. Revisar exemplos e testes que ainda fabricam gates com `status`.
Arquivos com evidência disso:
- `tests/test_evaluator.py`
- `examples/example_evaluator_release.py`

4. Definir um helper ou constante compartilhada para estados de gate.
O objetivo é evitar novos aliases como `status`, `state`, `result` para a mesma coisa.

5. Revisar `artifact_contracts.py` para garantir que contratos de artefatos não misturem nomenclatura do domínio de gate com nomenclatura de evaluation report.

### Validação obrigatória
```bash
pytest -q tests/test_pr01_schema_unification.py tests/test_evaluator.py
rg -n "get\(\"status\"|\[\"status\"\].*gate|GateResult\(" src tests examples
```

### Só pode seguir se
- `ReleaseReadinessEngine` não depender mais de `status` para gate result
- nenhum teste essencial de gate estiver montando payload divergente sem motivo explícito
- a nomenclatura estiver estável em código e exemplos

## PR-02. Fechar contrato real dos artefatos

### Objetivo operacional
Fazer a árvore de artefatos produzida pelo sistema bater com a documentação e com os consumidores.

### Arquivos-alvo
- `src/cvg_harness/research/research_agent.py`
- `src/cvg_harness/prd/prd_agent.py`
- `src/cvg_harness/spec_builder/spec_builder.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `docs/0007-contratos-dos-artefatos.md`
- `tests/test_pr02_canonical_artifacts.py`

### Decisão que precisa ser tomada
Escolher um dos dois modelos e aplicar sem ambiguidade:
- modelo A: `md` para humano e `json` sidecar para máquina
- modelo B: somente um formato por artefato, exceto `spec`

Recomendação: manter modelo A, porque o código já evoluiu nessa direção.

### Passo a passo
1. Listar os artefatos realmente gerados no workspace durante o fluxo.
2. Comparar essa lista com `docs/0007-contratos-dos-artefatos.md`.
3. Atualizar `artifact_contracts.py` para refletir o modelo canônico escolhido.
4. Atualizar `docs/0007` para declarar explicitamente quando existe par `md + json`.
5. Garantir que `version` e `change_reason` existam em todos os artefatos mutáveis definidos como versionados.
6. Garantir que o orquestrador salve e consuma o artefato certo em cada etapa.

### Validação obrigatória
```bash
pytest -q tests/test_pr02_canonical_artifacts.py
rg -n "research-notes\\.(md|json)|system-map\\.(md|json)|prd\\.(md|json)|spec\\.(md|json)" src docs tests
```

### Só pode seguir se
- não houver artefato “oficial” sem contrato
- não houver contrato sem artefato correspondente
- docs e código declararem o mesmo conjunto de extensões

## PR-03. Fechar o fluxo fim a fim no `FlowOrchestrator`

### Objetivo operacional
Sair de “métodos isolados” e chegar a um fluxo coerente que gere todos os artefatos mínimos de cada fase.

### Arquivos-alvo
- `src/cvg_harness/flow.py`
- `src/cvg_harness/sprint/sprint_planner.py`
- `src/cvg_harness/contracts/handoff.py`
- `src/cvg_harness/ledger/progress_ledger.py`
- `src/cvg_harness/ledger/event_log.py`
- `tests/test_pr03_flow_orchestrator.py`
- `tests/test_integration.py`

### Passo a passo
1. Criar persistência explícita de `execution-order.json` a partir de `SprintPlan.execution_order`.
Não deixar essa informação só embutida em `sprint-plan.json`.

2. Adicionar um método explícito de release no orquestrador.
Hoje existe `check_release_readiness()`, mas o fluxo documentado pede uma etapa de release clara.

3. Garantir que cada método principal do fluxo faça três coisas:
- produza o artefato da etapa
- atualize `flow-state.json`
- registre evento no `event-log.jsonl`

4. Garantir que handoff seja criado na transição entre etapas relevantes, não apenas em partes do fluxo.

5. Garantir que o fluxo mínimo FAST rode nesta ordem:
- classify
- research
- prd
- build_spec
- run_lint
- plan_sprints
- check_guard ou etapa equivalente durante execução
- evaluate_sprint
- detect_drift
- release

6. Revisar a regra de sprint ativa única.
Hoje existe `state.sprint_id`, mas isso não é suficiente como enforcement.

### Validação obrigatória
```bash
pytest -q tests/test_pr03_flow_orchestrator.py tests/test_integration.py
rg -n "execution-order\.json|release-readiness-report|current_gate|current_phase|event-log" src/cvg_harness/flow.py src/cvg_harness/sprint/sprint_planner.py
```

### Só pode seguir se
- `execution-order.json` existir de verdade
- o fluxo mínimo gerar artefatos sem injeção manual de estado
- houver evento correspondente para cada avanço relevante de fase/gate

## PR-04. Integrar gates, fallback e replan ao fluxo real

### Objetivo operacional
Parar de tratar gate como metadado passivo e transformá-lo em decisão formal persistida.

### Arquivos-alvo
- `src/cvg_harness/gates/gate_policy.py`
- `src/cvg_harness/flow.py`
- `src/cvg_harness/fallback/fallback_policy.py`
- `src/cvg_harness/replan/replan_coordinator.py`
- `tests/test_pr04_gates_fallback.py`

### Passo a passo
1. Definir um padrão único para persistência de gate result.
Recomendação: salvar em `reports/gates/GATE_N.json`.
Não manter o padrão implícito e estranho de `gate-gate_0.json`.

2. Em cada etapa do fluxo, chamar `evaluate_gate()` com o artefato correto.
Exemplo mínimo:
- `GATE_0` após `classification.json`
- `GATE_1` após research
- `GATE_2` após PRD
- `GATE_3` após SPEC
- `GATE_4` após lint
- `GATE_5` após sprint plan
- `GATE_6` após architecture guard
- `GATE_7` após evaluation
- `GATE_8` após drift
- `GATE_9` após release readiness

3. Persistir o resultado formal do gate e também registrar evento correspondente.

4. Ajustar fallback para que toda reprovação material gere:
- bloqueio de estado, quando aplicável
- evento operacional
- decisão de retry ou replan

5. Fechar o caminho de `misclassification` para emitir `replan_requested` quando o caso acontecer.

6. Definir comportamento formal para `waived`.
Se `waived` existir, ele precisa ser reconhecido por:
- gate policy
- flow state
- release readiness
- testes

### Validação obrigatória
```bash
pytest -q tests/test_pr04_gates_fallback.py
rg -n "evaluate_gate|save_gate_result|replan_requested|waived|fallback-events" src tests
```

### Só pode seguir se
- houver arquivo de resultado para os gates relevantes
- release não depender mais de resultado de gate inexistente
- `replan_requested` estiver saindo do fluxo real, não só do contrato

## PR-05. Fechar mecanismos críticos de controle

### Objetivo operacional
Eliminar stubs, ampliar cobertura mínima real e impedir falso senso de governança.

### Arquivos-alvo
- `src/cvg_harness/guardian/architecture_guardian.py`
- `src/cvg_harness/drift/drift_detector.py`
- `src/cvg_harness/evaluator/evaluator.py`
- `tests/test_pr05_guardian_drift.py`

### Passo a passo
1. Implementar `_check_unauthorized_boundary_change()`.
Mesmo que a heurística inicial seja simples, ela precisa verificar algo real.
Sugestão mínima:
- se um arquivo alterado cair em boundary declarada e a boundary não estiver autorizada pela SPEC, registrar violação `fail`

2. Adicionar camada `avaliacao_x_release_readiness` no `DriftDetector`.
Sugestão mínima:
- se `evaluation.result == FAILED` e `release.decision == APPROVED`, gerar finding alto
- se houver `evidence_missing` e release não carregar risco residual correspondente, gerar finding médio ou alto

3. Fortalecer `Evaluator` para validar contrato mínimo.
Hoje ele só olha `criterios` e uma lista fixa de evidências.
Ele deve validar pelo menos:
- critérios esperados pela sprint
- evidências obrigatórias declaradas
- edge cases presentes na SPEC
- falha contratual quando artefato esperado não existe

4. Adicionar testes negativos específicos para cada um desses cenários.

### Validação obrigatória
```bash
pytest -q tests/test_pr05_guardian_drift.py tests/test_evaluator.py
rg -n "pass$|evaluation x release|evidence_missing|edge_cases|contrato" src/cvg_harness/guardian src/cvg_harness/drift src/cvg_harness/evaluator
```

### Só pode seguir se
- não restar `pass` em regra crítica declarada como mínima
- drift conseguir acusar conflito entre avaliação e release
- evaluator reprovar ausência real de evidência ou artefato

## PR-06. Fechar release, métricas e runtime mínimo

### Objetivo operacional
Tirar a camada final do estado “nominal” e deixá-la operacional o suficiente para consumo real.

### Arquivos-alvo
- `src/cvg_harness/release/release_readiness.py`
- `src/cvg_harness/flow.py`
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `src/cvg_harness/auto_runtime/runtime_automation.py`
- `tests/` novos para `PR-06`

### Passo a passo
1. Escolher o artefato final canônico de release.
No estado histórico da auditoria, a documentação apontava para `release-readiness.md`.
Hoje, o canônico consolidado é `release-readiness-report.json` com `release-readiness.md` opcional como sidecar legível por humano.

2. (estado histórico) Parar de salvar somente `release-readiness-report.json` em `flow.py`.
Salvar o artefato canônico decidido e alinhar consumers.

3. Ajustar `ReleaseReadinessEngine` para consolidar:
- gates reais
- exceções reais
- riscos residuais reais
- waivers reais

4. Reescrever `MetricsAggregator` para usar eventos reais.
Lead time deve vir de timestamps do fluxo.
Retrabalho deve vir de rounds, retries ou replans registrados.
Não usar fórmulas arbitrárias sem base em eventos.

5. Dar ao `RuntimeExecutor` um modo mínimo executável.
Opções aceitáveis:
- executar subprocess com timeout e capturar código de saída
- ou implementar um contrato explícito de simulação com `status: simulated`

O que não é aceitável:
- continuar retornando `not_executed` para todo caso e chamar isso de runtime integration

6. Se hooks forem obrigatórios, falha de hook precisa virar evento e potencial blocker.

### Validação obrigatória
```bash
pytest -q
rg -n "release-readiness-report|estimatedCostUsd / 10|not_executed|simulated|subprocess" src tests
```

### Só pode seguir se
- o release final consumir gates corretos
- as métricas tiverem rastreabilidade para eventos
- runtime mínimo produzir resultado observável por artefato, status ou log

## PR-07. Fechar comunicação pública

### Objetivo operacional
Fazer README, examples e claims refletirem exatamente o estado real do código.

### Arquivos-alvo
- `README.md`
- `examples/demo_complete_flow.py`
- `examples/example_evaluator_release.py`
- `tests/` novos de smoke test, se fizer sentido

### Passo a passo
1. Revisar a tabela de status do README.
Se `PR-06` e `PR-07` não estiverem fechadas, não marcar `✅`.

2. Remover claims absolutas como “orquestração completa” enquanto o fluxo ainda depender de injeção manual ou etapas não persistidas.

3. Revisar `examples/demo_complete_flow.py`.
Eliminar trechos onde o exemplo injeta caminho manualmente no estado para compensar ausência do fluxo real.

4. Se um exemplo ainda depender de simplificação, declarar isso no próprio exemplo.

5. Se possível, converter exemplos principais em smoke tests leves.

### Validação obrigatória
```bash
rg -n "orquestração completa|PR-06|PR-07|manual|inject|state\.spec_path|state\.prd_path" README.md examples
pytest -q tests
```

### Só pode encerrar o trabalho se
- README não contradizer o código
- examples rodarem sem gambiarra de estado para o caminho principal demonstrado
- a documentação pública usar linguagem proporcional ao que está implementado

## Critério de conclusão final
Só considerar o projeto “fechado contra o backlog” quando todos os pontos abaixo forem verdadeiros ao mesmo tempo:
- o orquestrador gerar os artefatos mínimos prometidos
- todos os gates relevantes tiverem resultado persistido
- release readiness consolidar dados reais, não inferidos por alias incompatível
- métricas vierem do event log e do estado do fluxo
- runtime mínimo deixar de ser placeholder universal
- README e examples refletirem a maturidade real

## Checklist rápido para o executor
- Corrigi schema ou só mascarei a divergência?
- Atualizei produtor, consumidor, contrato e teste no mesmo passo?
- O artefato prometido existe de verdade no workspace?
- O gate foi só “marcado” no estado ou realmente avaliado e persistido?
- A métrica veio de timestamp/evento real ou de fórmula arbitrária?
- O README continua prometendo mais do que o código entrega?

Se alguma dessas respostas for “mas mais ou menos”, a etapa ainda não está fechada.
