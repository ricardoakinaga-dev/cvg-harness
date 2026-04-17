# 0033. Sprint 13 - Observabilidade e canonicidade do event log

## Objetivo
Fechar o último resíduo pequeno de observabilidade formal que ainda aparece na trilha documental: alinhar a orquestração do fluxo aos eventos canônicos já definidos em `docs/0010-progress-ledger-e-event-log.md`, sem mexer em release, gates ou lifecycle terminal.

## Estado de partida
- O projeto segue aprovado e a trilha de consolidação anterior está fechada.
- `pytest -q` e `python3 examples/demo_complete_flow.py` permanecem verdes no estado atual.
- O contrato canônico de eventos já existe em `src/cvg_harness/types.py` e `docs/0010-progress-ledger-e-event-log.md`.
- A implementação do `FlowOrchestrator` ainda emite o fluxo principal, mas não materializa alguns eventos de entrada previstos no contrato, em especial:
  - `demand_received`
  - `research_started`
- O resíduo é pequeno e localizado: semântica e ordem do event log, não comportamento de produto.

## Itens do sprint (execução limitada a este bloco)

### 1) Emitir eventos canônicos de início de fluxo
**Status:** `done`

Arquivos alvo:
- `src/cvg_harness/flow.py`
- `tests/test_flow.py`
- `tests/test_progress.py`

Mudanças esperadas:
- registrar `demand_received` no ponto em que o fluxo começa a ser materializado de forma observável;
- registrar `research_started` no início da fase de research;
- preservar os eventos já existentes e a ordem do fluxo;
- manter `last_event` e `progress.json` coerentes com o estado real.

Critérios de saída:
- o event log passa a conter os eventos canônicos de entrada previstos no contrato;
- a sequência observável fica mais próxima da trilha documental, sem reclassificar fases já estáveis;
- os testes cobrem presença e ordem mínima dos eventos.

### 2) Atualizar a documentação de evento e cobertura de regressão
**Status:** `done`

Arquivos alvo:
- `docs/0010-progress-ledger-e-event-log.md`
- `tests/test_flow.py`
- `tests/test_progress.py`

Mudanças esperadas:
- registrar de forma explícita onde `demand_received` e `research_started` são emitidos;
- alinhar exemplos e texto de contrato com a sequência real do fluxo;
- adicionar cobertura de regressão para impedir drift entre contrato canônico e implementação.

Critérios de saída:
- a documentação deixa de sugerir um event log mais completo do que a implementação atual;
- os testes passam a blindar a sequência canônica mínima.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
pytest -q tests/test_flow.py tests/test_progress.py
rg -n "demand_received|research_started|event-log|progress.json|waiver_granted|release_rejected" src docs tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- `FlowOrchestrator` emite os eventos de entrada canônicos esperados.
- `docs/0010-progress-ledger-e-event-log.md` descreve o comportamento real, sem inflar o contrato.
- a mudança permanece incremental e não afeta release, gates, SPEC ou planejamento.
- Próxima rodada incremental registrada em `docs/0035-sprint-14-contratos-criticos-no-spec-builder.md`.
