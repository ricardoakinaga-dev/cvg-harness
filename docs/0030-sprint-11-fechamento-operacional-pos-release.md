# 0030. Sprint 11 — Fechamento operacional e coerência de estado pós-release

## Nota de rastreabilidade
Este documento foi absorvido operacionalmente pela execução consolidada em `docs/0029-sprint-10-fechamento-de-ciclo-e-coerencia-operacional.md`.
Ele permanece no repositório apenas para preservar a trilha histórica de uma rodada intermediária focada no fechamento terminal pós-release.

## Objetivo
Fechar uma rodada curta para tornar o fim do fluxo canônico observável e consistente após `release_approved`, sem reabrir aprovação já conquistada.

## Estado de partida
- Projeto continua aprovado.
- Validação rápida executada antes desta sprint:
  - `pytest -q` → 172 testes passando
  - `python3 examples/demo_complete_flow.py` executado com sucesso
- Resíduo mapeado no estado de partida da sprint (histórico desse ciclo):
  - release é aprovado, mas `flow-state` permanece em `status=running` e `current_phase=sprint`;
  - o estado final não fecha de forma explícita no artefato operacional;
  - leitura pública do encerramento (demo + progress) ainda pode parecer "ainda em andamento".
- Esse resíduo foi alvo desta sprint e é tratado integralmente nos itens abaixo.

## Foco da sprint
Corrigir apenas a coerência terminal de execução e a sincronização entre `flow-state`, `progress.json` e a evidência exibida no demo.

## Itens do sprint

### 1) Finalizar estado do fluxo após decisão de release
**Status:** `done`

Objetivo:
- tornar o estado final explícito quando a decisão de release é produzida.

Arquivos alvo:
- `src/cvg_harness/flow.py`

Mudanças esperadas:
- em `check_release_readiness()`, após `release_approved`, definir:
  - `state.current_phase = "release"`
  - `state.status = "completed"`
  - `state.blockers = []`
- em `release_rejected`, manter:
  - `state.current_phase = "release"`
  - `state.status = "blocked"`
  - `state.blockers` contendo `release_rejected` (sem regressão)
- preservar evento canônico atual (`release_approved` / `release_rejected`).

Critérios de saída:
- release aprovado termina com `status="completed"` e `current_phase="release"`.
- release rejeitado termina com `status="blocked"` e `current_phase="release"`.

### 2) Sincronizar progress ao fechamento do ciclo
**Status:** `done`

Objetivo:
- garantir que o fim da execução fique refletido no `progress.json`.

Arquivos alvo:
- `src/cvg_harness/flow.py`
- `src/cvg_harness/ledger/progress_ledger.py` (se necessário para mapear estado final sem quebrar contratos atuais)

Mudanças esperadas:
- chamar `sync_progress()` após `check_release_readiness()`;
- validar mapeamento de status de `flow-state` para `progress.status` no estado final (running → in_progress, completed/blocked refletidos corretamente).
- manter `current_gate` e `current_sprint` consistentes com o estado final.

Critérios de saída:
- `progress.json` pode ser carregado após release e refletir o estado final do fluxo.
- `status` no progress não indica andamento quando o fluxo foi aprovado.

### 3) Ajustar evidência de encerramento do demo
**Status:** `done`

Objetivo:
- deixar o encerramento da execução didática consistente com o estado real de finalização.

Arquivos alvo:
- `examples/demo_complete_flow.py`
- `docs/0008-gates-e-politica-de-aprovacao.md` (ajuste de frase, se necessário, sem mudar a política)

Mudanças esperadas:
- usar `orch.state.status`/`orch.state.current_phase` apenas como estado final já alinhado;
- imprimir mensagem explícita de ciclo finalizado;
- remover ambiguidade de “executado com sucesso” quando o fluxo estiver tecnicamente encerrado.

Critérios de saída:
- o leitor do exemplo entende claramente se o ciclo terminou aprovado e finalizado ou bloqueado.

## Arquivos alvo prioritários
- `src/cvg_harness/flow.py`
- `src/cvg_harness/ledger/progress_ledger.py`
- `examples/demo_complete_flow.py`
- `tests/test_pr03_flow_orchestrator.py`
- `tests/test_progress.py`

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "release_approved|release_rejected|status=running|current_phase|completed|progress.json|FlowOrchestrator|release-readiness-report.json|aprovada" docs README.md examples tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- `check_release_readiness()` passa a emitir estado terminal explícito e consistente.
- `progress.json` e `flow-state` convergem para leitura única do estado final.
- demo deixa claro o estado final do ciclo (aprovado/encerrado vs bloqueado).
- nenhum comportamento estrutural fora desse escopo é alterado; sprint permanece focada em rastreabilidade operacional.

## Encerramento
**Sprint 11 concluída — 2026-04-16.**

Evidência executada nesta sequência:
- `pytest -q` com sucesso (172 testes passando).
- `python3 examples/demo_complete_flow.py` com estado final `Fluxo: completed`.
- estado persistido com `status=completed` e `current_phase=release` no passo de fluxo final.

## Encadeamento
- Sprint anterior de consolidação: `docs/0020-sprint-03-consolidacao-documental.md`.
- Consolidação operacional final desta frente: `docs/0029-sprint-10-fechamento-de-ciclo-e-coerencia-operacional.md`.
