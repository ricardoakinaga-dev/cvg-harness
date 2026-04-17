# 0038. Sprint 16 - Endurecimento Guardian + Drift

## Objetivo
Executar uma rodada curta para aumentar o rigor de `Architecture Guardian` e `Drift Detector`, atacando o principal gap remanescente apontado na auditoria `0037` sem reabrir planning, contratos básicos, métricas canônicas ou release já estabilizados.

## Estado de partida
- O projeto segue aprovado e estável após as Sprints 14 e 15.
- Auditoria mais recente em `docs/0037-relatorio-de-auditoria-pos-sprint-15.md` elevou a nota global para `87/100`.
- Os menores subscores do núcleo operacional no início desta sprint eram:
  - `Architecture Guardian` -> `77/100`
  - `Drift Detector` -> `76/100`
  - `Evaluator / QA Gate` -> `78/100`
- O estado validado na abertura foi:
  - `pytest -q` -> `200/200`
  - `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`

## Foco da sprint
Atacar apenas endurecimento de guard, drift e sua observabilidade mínima.

## Itens do sprint

### 1. Aumentar precisão do `Architecture Guardian`
**Status:** `done`

Arquivos alvo:
- `src/cvg_harness/guardian/architecture_guardian.py`
- `src/cvg_harness/flow.py`
- `tests/test_pr05_guardian_drift.py`
- `tests/test_pr03_flow_orchestrator.py`

Resultado desta rodada:
- `ArchitectureGuardian` passou a usar matching por prefixo de caminho, em vez de substring solta;
- touch em `boundary` sensível dentro de área autorizada passa a gerar `WAIVER`, enquanto touch fora do escopo segue como `FAIL`;
- `FlowOrchestrator.check_guard()` passou a emitir `architecture_guard_waived` e incluir regras disparadas no payload do evento;
- a suíte ganhou cobertura para boundary waiver, autorização explícita de boundary e matching de escopo por prefixo.

### 2. Tornar o `DriftDetector` mais explicativo
**Status:** `done`

Arquivos alvo:
- `src/cvg_harness/drift/drift_detector.py`
- `src/cvg_harness/flow.py`
- `tests/test_drift.py`
- `tests/test_pr05_guardian_drift.py`
- `tests/test_pr03_flow_orchestrator.py`

Resultado desta rodada:
- `DriftDetector` passou a registrar root cause e remediation mais específicas por camada;
- a checagem `evaluation x release readiness` ficou ativa no fluxo real quando `evaluation-report.json` e `release-readiness-report.json` existem;
- drift entre SPEC e sprint plan agora aceita cobertura por prefixo de caminho para módulos aninhados;
- falhas de avaliação com arquivos alterados mas evidência faltando passam a registrar causalidade mais explícita;
- o evento de drift passou a carregar quantidade de findings e severidade máxima observada.

### 3. Consolidar cobertura e trilha documental
**Status:** `done`

Arquivos alvo:
- `docs/0037-relatorio-de-auditoria-pos-sprint-15.md`
- `tests/test_drift.py`
- `tests/test_pr05_guardian_drift.py`
- `tests/test_pr03_flow_orchestrator.py`

Resultado desta rodada:
- a cobertura nova tornou reprodutível o endurecimento de `guardian` e `drift` sem mexer em planning, release ou métricas canônicas;
- a trilha documental foi consolidada com auditoria de saída desta sprint;
- o ciclo fechou sem regressão no demo principal.

## Validação
```bash
pytest -q
pytest --collect-only -q
python3 examples/demo_complete_flow.py
pytest -q tests/test_drift.py tests/test_pr05_guardian_drift.py tests/test_pr03_flow_orchestrator.py -rA
```

## Critério de encerramento
- `Architecture Guardian` usa boundaries e arquivos alterados com mais precisão;
- `DriftDetector` explica melhor causa e severidade do desalinhamento;
- a cobertura e a trilha documental deixam o avanço explícito;
- o escopo permanece incremental, sem reabrir fluxo, release, planning ou métricas já estabilizados.

## Validação executada
- Focada: `pytest -q tests/test_drift.py tests/test_pr05_guardian_drift.py tests/test_pr03_flow_orchestrator.py` -> `42/42`.
- Completa: `pytest -q` -> `200/200`.
- Coleta: `pytest --collect-only -q` -> `200 tests collected`.
- Demo: `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`.

## Encadeamento
- Auditoria de entrada: `docs/0037-relatorio-de-auditoria-pos-sprint-15.md`.
- Auditoria de saída: `docs/0039-relatorio-de-auditoria-pos-sprint-16.md`.
