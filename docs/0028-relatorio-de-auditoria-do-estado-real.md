# 0028. Relatório de auditoria do estado real do CVG Harness

## Objetivo
Registrar uma auditoria do estado real do projeto com base em:
- documentação da pasta `docs/`
- implementação atual em `src/`
- suíte de testes
- execução do demo principal

> Nota: este relatório é histórico e não representa o estado corrente final.

## Evidências executadas
```bash
pytest -q
python3 examples/demo_complete_flow.py
```

Resultado observado nesta auditoria:
- `pytest -q` -> `172/172` testes passando
- `examples/demo_complete_flow.py` -> `APPROVED`, `10/10` gates persistidos, `pass rate 100%`

## Achados principais

### 1. Fechamento do ciclo operacional na data dessa auditoria
Severidade: alta

No momento desta auditoria (na sequência anterior ao encerramento completo de terminalização):
- `flow-state.json` permanece com `status=running`
- a fase final continua `sprint`
- `progress.json` não é resincronizado após `check_release_readiness()`

Impacto:
- a esteira entrega decisão de release, mas não materializa encerramento completo do lifecycle
- isso enfraqueceu a rastreabilidade operacional prometida nos docs fundacionais
- o resíduo foi tratado em `docs/0029-sprint-10-fechamento-de-ciclo-e-coerencia-operacional.md` e consolidado em `docs/0030-sprint-11-fechamento-operacional-pos-release.md`.

Arquivos centrais:
- `src/cvg_harness/flow.py`

### 2. Motores de planning ainda são heurísticos demais
Severidade: alta

`ResearchAgent`, `PRDAgent` e `SpecBuilderAgent` produzem artefatos úteis, mas ainda simplificados.
A profundidade real está abaixo do que `0005`, `0006` e `0007` sugerem.

> Atualização posterior: este gap foi atacado incrementalmente em `docs/0031-sprint-12-profundidade-dos-motores-de-planning.md`, com desdobramento operacional em `docs/0032-sprint-12-01-evidencia-real-no-research-agent.md`. O item permanece neste relatório por fidelidade histórica ao estado auditado na data original.

Sinais:
- research infere módulos por palavras-chave
- PRD usa montagem bastante genérica
- SPEC nasce com contratos quase vazios e critérios derivados de templates simples

Impacto:
- boa aderência de framework
- aderência parcial como “sistema operacional de engenharia” mais profundo

Arquivos centrais:
- `src/cvg_harness/research/research_agent.py`
- `src/cvg_harness/prd/prd_agent.py`
- `src/cvg_harness/spec_builder/spec_builder.py`

### 3. Observabilidade formal ainda não fecha todo o contrato documental
Severidade: média

O fluxo já registra eventos relevantes, mas ainda há lacunas:
- `detect_drift()` define `last_event`, porém não grava `drift_clean`/`drift_detected` no `event-log.jsonl`
- `check_guard()` usa `sprint_approved` como `last_event` quando passa, o que mistura semântica de guard e evaluator

Impacto:
- event log útil, porém ainda não totalmente coerente com a documentação de telemetria/gates

Arquivos centrais:
- `src/cvg_harness/flow.py`
- `docs/0010-progress-ledger-e-event-log.md`

### 4. Release readiness ainda não exige todos os gates anteriores
Severidade: média

`ReleaseReadinessEngine` exige como obrigatórios:
- `GATE_0`, `GATE_1`, `GATE_2`, `GATE_3`, `GATE_4`, `GATE_5`, `GATE_7`, `GATE_9`

Hoje ficam fora da obrigatoriedade direta:
- `GATE_6`
- `GATE_8`

Impacto:
- a política real de release fica um pouco mais permissiva do que a narrativa documental sugere

Arquivos centrais:
- `src/cvg_harness/release/release_readiness.py`
- `docs/0008-gates-e-politica-de-aprovacao.md`

### 5. Há resíduos leves de qualidade textual no código
Severidade: baixa

Exemplos observados:
- `Manter耦合`
- `aguardarat`
- `ou供给`
- `Zero блокеров`

Impacto:
- não afeta funcionalidade central
- reduz qualidade percebida e maturidade de acabamento

Arquivos centrais:
- `src/cvg_harness/guardian/architecture_guardian.py`
- `src/cvg_harness/drift/drift_detector.py`
- `src/cvg_harness/prd/prd_agent.py`

## Notas por item analisado

### Núcleo operacional
- Visão geral / tese operacional: `84/100`
- Classificação FAST vs ENTERPRISE: `92/100`
- Research Engine: `48/100`
- PRD Engine: `58/100`
- Spec Builder: `63/100`
- Contratos de artefatos: `86/100`
- Spec Linter: `89/100`
- Sprint Planner: `81/100`
- Flow Orchestrator fim a fim: `74/100`
- Gates e política de aprovação: `82/100`
- Fallback e replanejamento: `85/100`
- Architecture Guardian: `77/100`
- Evaluator / QA Gate: `75/100`
- Drift Detector: `73/100`
- Release Readiness: `74/100`
- Progress Ledger + Event Log: `69/100`
- Runtime / hooks operacionais: `85/100`
- Metrics Aggregator: `72/100`

### Produto, documentação e extensões
- README + demos + examples: `86/100`
- Capacidades P2 de observabilidade/analytics: `64/100`
- Capacidades P3 estratégicas: `46/100`
- Aderência documental geral: `80/100`

## Nota global
`76/100`

## Leitura executiva
O projeto está em bom estado no núcleo, com forte cobertura de testes e demo funcional.
No momento dessa auditoria, o principal gap não era estabilidade básica, e sim diferença entre:
- o que a documentação fundacional promete
- e a profundidade operacional realmente materializada em alguns motores e no fechamento do lifecycle

## Próximo passo recomendado
Abrir um sprint curto focado em:
1. fechamento de ciclo após release
2. coerência de observabilidade/event log
3. alinhamento entre gates obrigatórios de release e política documental

Próximo ciclo documentado em:
- `docs/0029-sprint-10-fechamento-de-ciclo-e-coerencia-operacional.md`
