# 0018. Sprint 02 - Checklist de aprovação e patch plan

## Objetivo
Transformou a auditoria da entrega declarada como “PR-01 a PR-07 totalmente implementadas e validadas” em uma rodada objetiva de fechamento.

Na rodada original, esta sprint não partiu do pressuposto de que a entrega já estivesse aprovada.
Ela definiu exatamente:
- o que ainda impede aprovação
- o que precisa ser alterado no código
- em que arquivo mexer
- como validar cada correção
- quando a entrega pode finalmente ser marcada como aprovada

Use esta doc junto com:
- `docs/0016-backlog-executavel-de-correcao.md` como quadro de status
- `docs/0017-guia-operacional-para-fechar-divergencias.md` como manual operacional base

`0018` é a rodada de sprint derivada da auditoria mais recente.

## Nota de leitura
Este documento preserva o diagnóstico e o patch plan originais da Sprint 02 para fins de rastreabilidade.
As seções a seguir (`Checklist objetiva do que impede aprovação` e `Patch plan por arquivo`) representam histórico técnico da auditoria original.
O estado vigente é o veredito final desta doc (aprovada) e o status `approved` de cada bloqueio encerrado.
Limpeza documental residual e melhoria de consistência textual seguem na Sprint 03 documentada em `docs/0020-sprint-03-consolidacao-documental.md`.

## Decisão desta auditoria
A entrega **está aprovada** após Sprint 02 (2026-04-16).

O que foi resolvido:
- `GATE_0` a `GATE_9` todos formalmente avaliados e persistidos em `reports/gates/`
- `release-readiness-report.json` é canônico com sidecar MD opcional documentado
- `DriftDetector` cobre `evaluation_x_release_readiness` via `release_readiness` parameter
- `ArchitectureGuardian` enforce boundaries usando `changed_files` recebidos do fluxo
- `validate_artifact_on_disk()` valida arquivo real, não só dict
- `RuntimeExecutor` tem 11 testes dedicados, modo `simulated` testado
- README atualizado para 160 testes, sem claims contraditórias

## Resultado desta sprint
A pergunta “posso aprovar essa entrega?” foi respondida com `sim` sem ressalvas documentais.

## Checklist objetivo histórico do que impede aprovação

### Histórico do Bloqueio 1. Gates formais não estão fechados ponta a ponta
**Status atual:** `approved` ✅

Evidência (histórica):
- `src/cvg_harness/flow.py` avalia e persiste só `GATE_0`
- etapas seguintes só mudam `current_gate/current_phase`
- release tenta ler arquivos de gate que o fluxo não gera consistentemente

Na auditoria original, para aprovar precisou ser verdade ao mesmo tempo:
- `GATE_0` a `GATE_9` têm ponto formal de avaliação
- os resultados são persistidos em caminho padronizado
- o release consome esses resultados reais
- o event log registra a aprovação/reprovação correspondente

Arquivos centrais:
- [flow.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/flow.py:65)
- [gate_policy.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/gates/gate_policy.py:132)

### Histórico do Bloqueio 2. Contrato de release continua divergente do output real
**Status atual:** `approved` ✅

Evidência (histórica):
- contrato declara `release-readiness.md`
- fluxo salva `release-readiness-report.json`
- engine de release continua serializando JSON puro

Na auditoria original, para aprovar precisou ser verdade ao mesmo tempo:
- artefato final de release ter nome canônico definido
- contrato, fluxo, exemplos e testes usarem o mesmo artefato
- se existir sidecar JSON, isso precisa estar documentado explicitamente

Arquivos centrais:
- [artifact_contracts.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/contracts/artifact_contracts.py:197)
- [flow.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/flow.py:456)
- [release_readiness.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/release/release_readiness.py:45)

### Histórico do Bloqueio 3. `DriftDetector` ainda não cobre a última camada declarada
**Status atual:** `approved` ✅

Evidência (histórica):
- docstring promete `avaliação x release readiness`
- assinatura de `detect()` não recebe artefato de release
- nenhuma checagem dessa camada existe hoje

Na auditoria original, para aprovar precisou ser verdade ao mesmo tempo:
- `detect()` aceitar dados de release
- a camada `avaliacao_x_release_readiness` existir de fato
- conflito entre `evaluation=FAILED` e `release=APPROVED` gerar finding detectável

Arquivos centrais:
- [drift_detector.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/drift/drift_detector.py:43)

### Histórico do Bloqueio 4. Boundary enforcement do guardian ainda é heurístico demais
**Status atual:** `approved` ✅

Evidência (histórica):
- `_check_unauthorized_boundary_change()` não recebe `changed_files`
- a detecção atual depende de relação indireta entre `boundaries` e `prohibited_areas`
- o `FlowOrchestrator` nem passa `boundaries` da SPEC ao guardian

Na auditoria original, para aprovar precisou ser verdade ao mesmo tempo:
- boundary change usar arquivos realmente alterados
- boundaries da SPEC serem carregadas pelo fluxo
- tocar boundary não autorizada produzir violação reproduzível em teste

Arquivos centrais:
- [architecture_guardian.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/guardian/architecture_guardian.py:98)
- [flow.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/flow.py:136)

### Histórico do Bloqueio 5. Validação de artefato ainda é apenas estrutural em memória
**Status atual:** `approved` ✅

Evidência (histórica):
- `validate_artifact()` só recebe `dict`
- não há verificação de arquivo salvo, extensão, pareamento `md/json`, artefatos vizinhos ou coerência mínima de persistência

Na auditoria original, para aprovar precisou ser verdade ao mesmo tempo:
- existir validação explícita de arquivo real ou helper equivalente
- contratos principais terem teste contra payload e persistência
- artefatos prometidos no contrato existirem quando o fluxo roda

Arquivos centrais:
- [artifact_contracts.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/contracts/artifact_contracts.py:224)

### Histórico do Bloqueio 6. RuntimeExecutor ainda não está “fully validated”
**Status atual:** `approved` ✅

Evidência (histórica):
- existe `subprocess.run()`, mas sem testes dedicados
- o caminho especial para `curl` é frágil com `shell=False`
- o runtime ainda não está integrado ao fluxo, gate ou event log

Na auditoria original, para aprovar precisou ser verdade ao mesmo tempo:
- haver testes específicos de execução real e simulada
- hooks obrigatórios poderem falhar de modo observável
- o caminho de execução não depender de comportamento incidental do subprocess

Arquivos centrais:
- [runtime_automation.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/auto_runtime/runtime_automation.py:60)

### Histórico do Bloqueio 7. A documentação pública continua superestimando a entrega
**Status atual:** `approved` ✅

Evidência (histórica):
- README marca `PR-07` como `✅`
- README ainda fala em `147 testes`, mas a suíte atual está em `148`
- a claim “README alinhado ao estado real” não se sustenta contra a auditoria

Na auditoria original, para aprovar precisou ser verdade ao mesmo tempo:
- README não contradizer mais o código
- números de testes e status refletirem o estado atual
- exemplos principais não mascararem gaps conhecidos

Arquivos centrais:
- [README.md](/home/ricardo/.openclaw/workspace/cvg-harness/README.md:127)
- [demo_complete_flow.py](/home/ricardo/.openclaw/workspace/cvg-harness/examples/demo_complete_flow.py:1)

## Patch plan por arquivo (histórico de implementação)

### Bloco A. Gates formais e release

#### 1. `src/cvg_harness/flow.py`
Objetivo histórico:
- fazer o fluxo avaliar e persistir gates de verdade
- parar de depender de estado implícito para aprovação

Mudanças necessárias originalmente:
- criar helper interno para avaliar e persistir gate, por exemplo `_evaluate_and_save_gate(gate_name, artifact_data)`
- padronizar caminho dos gates, por exemplo `reports/gates/GATE_N.json`
- chamar esse helper em todos os pontos relevantes do fluxo:
  - após `classification.json` para `GATE_0`
  - após research para `GATE_1`
  - após PRD para `GATE_2`
  - após SPEC para `GATE_3`
  - após lint para `GATE_4`
  - após sprint planning para `GATE_5`
  - após guard para `GATE_6`
  - após evaluation para `GATE_7`
  - após drift para `GATE_8`
  - após release readiness para `GATE_9`
- `check_release_readiness()` deve ler esse diretório padronizado, não um padrão ad hoc `gate-gate_*.json`
- substituir `release-readiness-report.json` pelo artefato final canônico decidido
- se mantiver JSON, declarar sidecar explicitamente nos contratos e docs

Validação:
```bash
pytest -q tests/test_pr03_flow_orchestrator.py tests/test_pr04_gates_fallback.py tests/test_integration.py
rg -n "save_gate_result|gate-gate_|reports/gates|release-readiness-report" src/cvg_harness/flow.py
```

Critério de saída:
- o release não pode mais aprovar sem ter os gates anteriores disponíveis
- o demo deve mostrar mais de um gate persistido

#### 2. `src/cvg_harness/gates/gate_policy.py`
Objetivo histórico:
- fazer a política de gate cobrir o fluxo real, não só `GATE_0-4`

Mudanças necessárias originalmente:
- completar critérios mínimos para `GATE_5` a `GATE_9`
- suportar `waived` de forma consistente, se esse estado continuar válido
- garantir compatibilidade entre shape de `GateResult` e release engine

Validação:
```bash
pytest -q tests/test_pr01_schema_unification.py tests/test_pr04_gates_fallback.py
```

#### 3. `src/cvg_harness/release/release_readiness.py`
Objetivo histórico:
- consolidar release com artefatos reais e nomenclatura única

Mudanças necessárias originalmente:
- decidir se o canônico será `release-readiness.md` com sidecar JSON ou JSON com doc atualizada
- se `state` é o campo canônico de gate, manter isso também no resumo do release
- preencher `waivers` explicitamente em vez de deixar a lista sempre vazia
- rejeitar release se faltarem gates obrigatórios
- opcionalmente emitir um campo `missing_gates`

Validação:
```bash
pytest -q tests/test_evaluator.py
```

### Bloco B. Contratos e validação de artefato

#### 4. `src/cvg_harness/contracts/artifact_contracts.py`
Objetivo histórico:
- elevar `validate_artifact()` acima de simples presença de chaves

Mudanças necessárias originalmente:
- manter `validate_artifact()` atual para payload
- adicionar helper complementar, por exemplo `validate_artifact_file()` ou `validate_artifact_on_disk()`
- validar pelo menos:
  - nome de artefato conhecido
  - existência do arquivo
  - carregamento JSON quando o contrato for `.json`
  - pareamento esperado quando existir modelo `md + json`
  - campos obrigatórios básicos após carregar o conteúdo
- revisar contratos que ainda divergem do output atual, especialmente:
  - `evaluation-report.json`
  - `drift-report.json`
  - `release-readiness.md`
  - `delivery-metrics.json`

Validação:
```bash
pytest -q tests/test_pr02_canonical_artifacts.py tests/test_handoff.py
```

#### 5. `docs/0007-contratos-dos-artefatos.md`
Objetivo histórico:
- alinhar a documentação ao artefato realmente produzido

Mudanças necessárias originalmente:
- documentar o modelo canônico de persistência
- declarar explicitamente onde existe `md + json`
- alinhar contrato final de release ao artefato real
- alinhar contrato de `execution-order.json` ao shape efetivamente salvo

Validação:
- leitura manual comparando com `artifact_contracts.py`
- nenhum artefato oficial sem espelho documental

### Bloco C. Guardian e drift

#### 6. `src/cvg_harness/guardian/architecture_guardian.py`
Objetivo histórico:
- transformar boundary enforcement em checagem real

Mudanças necessárias originalmente:
- fazer `_check_unauthorized_boundary_change()` receber `changed_files`
- comparar `changed_files` contra `boundaries` e `authorized_areas`
- registrar violação quando arquivo tocar boundary não autorizada
- remover heurística indireta baseada em `prohibited_areas`
- corrigir texto com caractere estranho em `Manter耦合`

Validação:
```bash
pytest -q tests/test_guardian.py tests/test_pr05_guardian_drift.py
```

#### 7. `src/cvg_harness/flow.py`
Objetivo adicional:
- passar `boundaries` da SPEC ao guardian

Mudanças necessárias originalmente:
- carregar `spec.get("boundaries", [])` ou campo equivalente
- instanciar `ArchitectureGuardian(..., boundaries=boundaries)`

Validação:
- teste de integração onde boundary existe na SPEC e é violada

#### 8. `src/cvg_harness/drift/drift_detector.py`
Objetivo histórico:
- completar a última camada prometida

Mudanças necessárias originalmente:
- adicionar parâmetro `release_readiness: Optional[dict] = None` a `detect()`
- registrar `layers_checked.append("avaliacao_x_release_readiness")` quando houver os dois artefatos
- criar `_check_evaluation_release_readiness(evaluation, release_readiness)`
- detectar pelo menos:
  - `evaluation=FAILED` com `release=APPROVED`
  - `evidence_missing` sem risco residual correspondente
  - gate crítico reprovado mas release condicional/aprovado

Validação:
```bash
pytest -q tests/test_drift.py tests/test_pr05_guardian_drift.py
```

### Bloco D. Evaluator e fallback

#### 9. `src/cvg_harness/evaluator/evaluator.py`
Objetivo histórico:
- tornar a avaliação menos superficial

Mudanças necessárias originalmente:
- validar edge cases da SPEC quando existirem
- aceitar lista de evidências esperadas derivada da sprint ou da SPEC, não só lista fixa hardcoded
- falhar quando artefato obrigatório declarado não existir
- se `guard_report` vier reprovado, refletir isso também como falha contratual

Validação:
```bash
pytest -q tests/test_evaluator.py tests/test_pr05_guardian_drift.py
```

#### 10. `src/cvg_harness/fallback/fallback_policy.py`
Objetivo histórico:
- fechar a parte “fully implemented” da política de fallback

Mudanças necessárias originalmente:
- manter `retry_local/review_sprint/replan/block`
- explicitar cenário de `misclassification` no fluxo principal, não só na policy
- garantir que `waived` tenha comportamento documentado e testado

Validação:
```bash
pytest -q tests/test_fallback.py tests/test_pr04_gates_fallback.py
```

### Bloco E. Runtime e métricas

#### 11. `src/cvg_harness/auto_runtime/runtime_automation.py`
Objetivo histórico:
- transformar a claim de runtime real em algo auditável

Mudanças necessárias originalmente:
- corrigir execução do comando quando `cmd.startswith("curl")`
  - ou sempre usar lista de argumentos
  - ou usar `shell=True` com justificativa explícita e sanitização mínima
- adicionar persistência opcional de saída em `artifact_output`
- incluir resultado observável para hooks obrigatórios
- se o modo `simulated` continuar, mantê-lo como fallback explícito e testado

Validação:
```bash
pytest -q
rg -n "RuntimeExecutor|simulated|subprocess.run|artifact_output" src tests
```

Critério extra:
- criar testes dedicados para `RuntimeExecutor`, porque hoje não há cobertura específica

#### 12. `src/cvg_harness/metrics_agg/metrics_aggregator.py`
Objetivo histórico:
- sair de “menos arbitrário” para “rastreável o suficiente”

Mudanças necessárias originalmente:
- manter lead time por timestamp real dos eventos
- substituir estimativas fixas de retrabalho/custo por derivação ligada a eventos nomeados, ou declarar explicitamente campos como `estimated_*`
- incluir teste cobrindo pelo menos um log com timestamps distintos
- não considerar “fully validated” sem teste específico para agregação com eventos reais

Validação:
```bash
pytest -q tests/test_agents_extended.py
```

### Bloco F. README e examples

#### 13. `README.md`
Objetivo histórico:
- alinhar a comunicação pública ao estado real

Mudanças necessárias originalmente:
- não marcar `PR-07` como `✅` antes do fechamento real desta sprint
- atualizar contagem de testes para `148` ou automatizar esse número fora do README
- rebaixar claims absolutas se os bloqueios acima ainda existirem
- referenciar `0018` como auditoria de fechamento, se isso fizer sentido para o time

Validação:
```bash
rg -n "PR-07|147 testes|README alinhado ao estado real|orquestração completa" README.md
```

#### 14. `examples/demo_complete_flow.py`
Objetivo histórico:
- transformar o demo em evidência, não em narrativa otimista

Mudanças necessárias originalmente:
- o demo não deve imprimir `Decisão: APPROVED` se os gates formais ainda não existirem
- o demo deve demonstrar os gates persistidos reais
- se o fluxo terminar `blocked`, isso precisa aparecer como conclusão honesta, não como “executado com sucesso” no sentido de aprovação de entrega
- idealmente, converter o demo principal em smoke test verificável

Validação:
```bash
python3 examples/demo_complete_flow.py
```

## Ordem de execução desta sprint
1. `flow.py` + `gate_policy.py` + `release_readiness.py`
2. `artifact_contracts.py` + `docs/0007-contratos-dos-artefatos.md`
3. `architecture_guardian.py` + ajuste correspondente em `flow.py`
4. `drift_detector.py`
5. `evaluator.py` + `fallback_policy.py`
6. `runtime_automation.py` + `metrics_aggregator.py`
7. `README.md` + `examples/demo_complete_flow.py`

## Critério de aprovação final da sprint
A sprint só pode ser marcada como concluída quando todos os itens abaixo forem verdadeiros:
- `pytest -q` continua verde
- existe cobertura específica nova para os pontos realmente alterados
- gates formais são persistidos e consumidos pelo release
- release usa o artefato canônico documentado
- drift cobre `evaluation x release readiness`
- guardian acusa boundary change real
- runtime tem teste dedicado
- README não contradiz mais o código

## Comandos finais de validação
```bash
pytest -q
rg -n "gate-gate_|release-readiness-report|147 testes|README alinhado ao estado real|not_executed|pass$" src README.md examples docs tests -g '!**/__pycache__/**'
python3 examples/demo_complete_flow.py
```

## Veredito após esta sprint
**APROVADA** — Todos os 7 bloqueios resolvidos.

Comandos de validação retornam verde:
- `pytest -q` → 160 tests
- Demo aprova release com métricas coerentes
- README sem contradições materiais
- `release-readiness-report.json` é o canônico com sidecar MD opcional

## Pós-fechamento
- A aprovação desta sprint permanece válida.
- Resíduos documentais não bloqueantes passam a ser tratados como consolidação da Sprint 03.
