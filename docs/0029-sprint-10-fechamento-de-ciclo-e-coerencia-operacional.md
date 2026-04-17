# 0029. Sprint 10 - Fechamento de ciclo e coerência operacional

## Objetivo
Executar uma rodada curta para melhorar a coerência operacional do fluxo principal sem reabrir a aprovação histórica do projeto.

Foco desta sprint:
- fechamento correto do lifecycle após release
- coerência entre state, progress e event log
- alinhamento entre release readiness e política formal de gates

## Estado de partida
- Projeto segue aprovado na trilha `0019`.
- `pytest -q` e `python3 examples/demo_complete_flow.py` estão verdes.
- Auditoria atual registrada em `docs/0028-relatorio-de-auditoria-do-estado-real.md`.
- O gap dominante atual está na coerência operacional do fluxo, não na estabilidade básica do núcleo.

## Itens do sprint

### 1. Fechar lifecycle do fluxo após release
**Status:** `done`

Objetivo:
- garantir que release aprovada mude o fluxo para estado terminal coerente

Arquivos alvo:
- `src/cvg_harness/flow.py`
- `src/cvg_harness/ledger/progress_ledger.py`
- `tests/test_integration.py`
- `tests/test_pr03_flow_orchestrator.py`

Mudanças esperadas:
- `check_release_readiness()` deve atualizar `current_phase` para `release`
- release aprovada deve marcar `status=completed`
- release rejeitada deve manter `status=blocked`
- `progress.json` deve ser resincronizado ao final da decisão de release

Resultado desta rodada:
- `check_release_readiness()` agora move o fluxo para `current_phase=release`
- release aprovada agora fecha o fluxo com `status=completed`
- release rejeitada continua em `status=blocked`
- `progress.json` passou a ser resincronizado ao final da decisão de release

Critério de saída:
- `flow-state.json` e `progress.json` refletem o mesmo estado final após release
- demo não termina com `running` quando o release já foi aprovado

### 2. Normalizar observabilidade do fluxo principal
**Status:** `done`

Objetivo:
- garantir que eventos canônicos relevantes realmente apareçam no log

Arquivos alvo:
- `src/cvg_harness/flow.py`
- `src/cvg_harness/types.py`
- `src/cvg_harness/ledger/event_log.py`
- `docs/0010-progress-ledger-e-event-log.md`
- `tests/test_progress.py`

Mudanças esperadas:
- `detect_drift()` deve registrar `drift_clean` ou `drift_detected`
- sucesso do guardian não deve reutilizar semântica de `sprint_approved`
- a documentação deve refletir apenas eventos realmente emitidos no fluxo principal

Resultado desta rodada:
- `check_guard()` passou a emitir evento explícito `architecture_guard_passed` em sucesso
- `check_guard()` continua emitindo `architecture_guard_failed` em falha, agora com persistência explícita no log
- `detect_drift()` passou a registrar `drift_clean`/`drift_detected` no `event-log.jsonl`
- `progress.json` passou a ser sincronizado também após guard e drift
- `types.py`, `event_log.py`, `0010` e os testes agora compartilham o mesmo contrato de eventos

Critério de saída:
- `event-log.jsonl` fica coerente com o contrato vivo de eventos
- um leitor consegue rastrear release, drift e avaliação sem ambiguidade semântica

### 3. Alinhar release readiness com política formal de gates
**Status:** `done`

Objetivo:
- reduzir diferença entre a política documental de GATE_9 e a implementação real

Arquivos alvo:
- `src/cvg_harness/release/release_readiness.py`
- `src/cvg_harness/gates/gate_policy.py`
- `docs/0008-gates-e-politica-de-aprovacao.md`
- `tests/test_evaluator.py`

Mudanças esperadas:
- decidir explicitamente se `GATE_6` e `GATE_8` são obrigatórios para release
- alinhar essa decisão entre código, teste e documento
- evitar contrato implícito diferente do comportamento real

Resultado desta rodada:
- `ReleaseReadinessEngine` passou a tratar `GATE_6` e `GATE_8` como obrigatórios para a decisão final
- a documentação de `GATE_9` agora explicita fechamento de `GATE_0` a `GATE_8`
- a suíte ganhou cobertura para rejeição de release quando gates obrigatórios estiverem ausentes

Critério de saída:
- gates exigidos para release ficam claros e consistentes em todo o sistema

### 4. Higienização curta de qualidade textual
**Status:** `done`

Objetivo:
- remover resíduos de texto corrompido ou misto sem alterar comportamento

Arquivos alvo:
- `src/cvg_harness/guardian/architecture_guardian.py`
- `src/cvg_harness/drift/drift_detector.py`
- `src/cvg_harness/prd/prd_agent.py`

Resultado desta rodada:
- resíduos textuais mistos/corrompidos foram removidos de guardian, drift, PRD e research
- mensagens operacionais passaram a usar português consistente nos caminhos centrais do fluxo

Critério de saída:
- não restam strings visivelmente corrompidas nos caminhos centrais do fluxo

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "drift_clean|drift_detected|release_approved|release_rejected|status=running|current_phase|GATE_6|GATE_8|耦合|供给|блокеров" src README.md docs tests examples -g '!**/__pycache__/**'
```

## Critério de encerramento
- fluxo termina com estado coerente após release
- `progress.json`, `flow-state.json` e `event-log.jsonl` contam a mesma história
- política de gates obrigatórios de release fica explícita e consistente
- correções são incrementais e não reabrem a aprovação histórica

## Encerramento
**Sprint 10 concluída — 2026-04-16.**

Evidência executada nesta rodada:
- `pytest -q` com sucesso (`172/172`).
- `python3 examples/demo_complete_flow.py` com estado final `Fluxo: completed` e `Release: APPROVED`.
- `event-log.jsonl` com eventos canônicos de guard e drift (`architecture_guard_passed`, `drift_clean`/`drift_detected`).
- `ReleaseReadinessEngine` alinhado para exigir `GATE_0` a `GATE_9`, incluindo `GATE_6` e `GATE_8` como gates obrigatórios de fechamento.

Resultado consolidado desta sprint:
- lifecycle pós-release passa a fechar em estado terminal coerente;
- `flow-state.json`, `progress.json` e `event-log.jsonl` contam a mesma história operacional;
- política de gates obrigatórios de release ficou explícita e consistente;
- resíduos textuais nos caminhos centrais do fluxo foram removidos.

## Encadeamento
- Auditoria de entrada: `docs/0028-relatorio-de-auditoria-do-estado-real.md`.
- Documento redundante de transição: `docs/0030-sprint-11-fechamento-operacional-pos-release.md` (mantido apenas por rastreabilidade histórica).
- Próximo ciclo incremental aberto em `docs/0031-sprint-12-profundidade-dos-motores-de-planning.md`.
