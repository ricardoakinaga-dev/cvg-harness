# 0027. Sprint 09 - Coerência de telemetria operacional e guardrails de contrato

## Objetivo
Consolidar uma rodada curta para reduzir ruído de rastreabilidade sem alterar comportamento funcional do fluxo principal.

## Estado de partida
- Projeto aprovado após Sprint 02 e consolidado na trilha documental (status final em `0019`).
- `pytest -q` e `python3 examples/demo_complete_flow.py` estão verdes no estado atual.
- `0016`, `0018`, `0019`, `0020` e `0026` formam a trilha histórica já encerrada.
- O próximo ciclo deve ser claramente executável por um agente sem revisão de contexto extensa.

## Itens do sprint (máximo 3)

### 1. Padronizar telemetria canônica por evento
**Status:** `done`

Objetivo:
- confirmar que o conjunto canônico de eventos está alinhado entre código e documentação, sem criar novos eventos implícitos.

Arquivos alvo:
- [src/cvg_harness/types.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/types.py)
- [src/cvg_harness/ledger/event_log.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/ledger/event_log.py)
- [docs/0010-progress-ledger-e-event-log.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0010-progress-ledger-e-event-log.md)
- [tests/test_progress.py](/home/ricardo/.openclaw/workspace/cvg-harness/tests/test_progress.py)

Critério de saída:
- lista de `EVENT_TYPES` do contrato vivo e da documentação principal sem divergência;
- evento esperado fora da implementação real só aparece com status/observação de “futuro”.

Execução em 2026-04-16:
- `event_log.py` passou a reutilizar `EVENT_TYPES` canônico de `types.py`.
- `tests/test_progress.py` ganhou verificação de alinhamento entre registries.
- documento `0010` foi atualizado com referência explícita à fonte canônica.

### 2. Normalizar decisões de observabilidade na trilha de continuidade
**Status:** `done`

Objetivo:
- manter a cadeia de continuidade explícita (do histórico de aprovação ao novo ciclo) com foco em rastreabilidade.

Arquivos alvo:
- [docs/0019-checklist-final-de-aprovacao.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0019-checklist-final-de-aprovacao.md)
- [docs/0016-backlog-executavel-de-correcao.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0016-backlog-executavel-de-correcao.md)
- [docs/0026-sprint-08-higienizacao-estado-real-e-rastreabilidade-documental.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0026-sprint-08-higienizacao-estado-real-e-rastreabilidade-documental.md)

Critério de saída:
- `0026` aparece como histórico de fechamento e `0027` como próximo ciclo documentado;
- evita ambiguidade de cadeia em pontos de entrada de revisão.

Execução em 2026-04-16:
- `0016`, `0019` e `0026` continuam apontando para este ciclo com leituras não ambíguas:
  - `0019` mantém o veredito aprovado e registra este ciclo como continuidade ativa;
  - `0016` mantém sequência de PRs encerrados com `0027` como próximo ciclo;
  - `0026` permanece como histórico de fechamento com `0027` como ponto de continuidade.
- a trilha de observação documental ficou com semântica fechada: histórico em `0016`, `0018`, `0019`, `0020`, `0026`; execução corrente em `0027`.

### 3. Alinhar contrato de métricas e release para rastreabilidade de observabilidade
**Status:** `done`

Objetivo:
- documentar/validar de forma reexecutável como métricas e residual risk são derivados de artefatos reais, sem alterar semântica de aprovação.

Arquivos alvo:
- [src/cvg_harness/metrics_agg/metrics_aggregator.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/metrics_agg/metrics_aggregator.py)
- [src/cvg_harness/release/release_readiness.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/release/release_readiness.py)
- [src/cvg_harness/dashboard/dashboards.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/dashboard/dashboards.py)
- [tests/test_evaluator.py](/home/ricardo/.openclaw/workspace/cvg-harness/tests/test_evaluator.py)

Critério de saída:
- contrato de decisão e telemetria com regras já existentes fica explicitado para execução reprodutível;
- ausência de evidência explícita não reclassifica automaticamente em blocker.

Execução em 2026-04-16:
- `release/release_readiness.py` foi tratado como fonte de decisão final de prontidão com regras explícitas:
  - `APPROVED` só quando não há rejeição por gate obrigatório, ausência de gates críticos e sem drifts de alta severidade;
  - `CONDITIONAL` quando há `waived` com blocos informados;
  - `REJECTED` para gates rejeitados, gates obrigatórios ausentes e/ou falha de avaliação.
- `metrics_agg/metrics_aggregator.py` mantém cálculo rastreável:
  - `pass_rate` deriva de eventos reais (`sprint_approved` + `evaluation_passed` vs falhas);
  - `rounds` deriva de `evaluation_failed` e `sprint_failed`;
  - custo mínimo de `$50` permanece aplicado apenas para caminho aprovado sem métricas explícitas e sem retries;
  - `lead_time_hours`, `retrabalho_hours` e `failures_by_type` permanecem derivados de eventos.
- `dashboard/dashboards.py` segue a trilha de observabilidade já existente combinando estado vivo (`progress`) com `event log` real.
- `tests/test_evaluator.py` já contempla aprovação/conditional/rejeição de release readiness com base no contrato acima.

## Critérios de saída gerais
- todos os itens acima executáveis sem alteração de produto;
- trilha nova-documental continua compatível com `APROVADA` de Sprint 02 e `approved` por bloqueio;
- cobertura de validação mínima para execução do ciclo.

## Validação prévia (estado de início)
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "Sprint 03|Sprint 02|APROVADA|done|todo|release-readiness\.md|0018|0020|172 testes" docs README.md examples tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- itens 1 a 3 concluídos com evidências de rastreabilidade atualizadas;
- `0026` fica preservada como histórico encerrado;
- aprovação existente continua intacta e não é reaberta.

## Encerramento
- ✅ Item 1: `EVENT_TYPES` único e alinhado entre implementação e documentação.
- ✅ Item 2: Cadeia de continuidade documental normalizada para observabilidade.
- ✅ Item 3: Contrato de métricas e release readiness explicitado em linguagem reexecutável.
- Data: 2026-04-16


## Continuidade
- Auditoria posterior do estado real registrada em `docs/0028-relatorio-de-auditoria-do-estado-real.md`.
- Próximo ciclo incremental aberto em `docs/0029-sprint-10-fechamento-de-ciclo-e-coerencia-operacional.md`.
