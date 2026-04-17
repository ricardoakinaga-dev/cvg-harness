# 0019. Checklist final de aprovação

## Objetivo
Registrar, de forma curta e operacional, o que ainda precisa ser verdade para que a entrega possa ser aprovada sem ressalvas.

Use este documento junto com:
- `docs/0016-backlog-executavel-de-correcao.md`
- `docs/0018-sprint-02-checklist-e-patch-plan.md`

## Estado atual
Todos os bloqueios foram resolvidos. A entrega está **aprovada**.

Nota:
- a aprovação permanece válida
- ajustes documentais residuais seguem em `docs/0020-sprint-03-consolidacao-documental.md`
- melhorias incrementais já encaminhadas já foram registradas em `docs/0021-sprint-04-observabilidade-e-event-log.md`
- auditoria mais recente do estado real está em `docs/0046-relatorio-de-auditoria-pos-sprint-18.md`
- ciclo operacional incremental mais recente consolidado em `docs/0044-sprint-18-cli-canonico-de-operacao.md`
- ciclo incremental mais recente consolidado em `docs/0064-sprint-36-politicas-configuraveis-por-projeto.md`

## Bloqueios finais

### 1. Artefato final de release
**Status:** `approved` ✅

Resolução:
- Decision: `release-readiness-report.json` é o canônico (máquina)
- `release-readiness.md` existe como sidecar opcional (humano)
- `artifact_contracts.py` atualizado com contrato JSON e nota de sidecar MD
- `docs/0007` atualizado para refletir o modelo JSON + MD sidecar

Arquivos centrais:
- `src/cvg_harness/contracts/artifact_contracts.py`
- `src/cvg_harness/release/release_readiness.py`
- `docs/0007-contratos-dos-artefatos.md`

### 2. Trilha documental de aprovação
**Status:** `approved` ✅

Resolução:
- `0016`, `0018` e `0019` atualizados para refletir o estado final real
- Todos bloqueios removidos, todos os PRs marcados como `done`
- Veredito final: entrega **aprovada**

Arquivos centrais:
- `docs/0016-backlog-executavel-de-correcao.md`
- `docs/0018-sprint-02-checklist-e-patch-plan.md`
- `docs/0019-checklist-final-de-aprovacao.md`

### 3. Métricas coerentes no fluxo real
**Status:** `approved` ✅

Resolução:
- `pass_rate`: counting `sprint_approved` and `evaluation_passed` events; happy path (release approved + 0 failures) → 100%
- `rounds`: counting `evaluation_failed` + `sprint_failed`; happy path → 0
- `cost`: base $50/sprint when release approved with no explicit cost
- `flow.py` now emits `sprint_started` event for metrics, `sprint_approved` for evaluation pass
- Demo shows: pass_rate=100%, cost=$50.00, rounds=0 — coherent with approved release

Arquivos centrais:
- `src/cvg_harness/metrics_agg/metrics_aggregator.py`
- `src/cvg_harness/flow.py`
- `examples/demo_complete_flow.py`

### 4. Política final para edge cases
**Status:** `approved` ✅

Decisão formal (2026-04-16):
- Edge cases **não evidenciados passam** com status=`passed` e nota explicativa
- Edge cases **evidenciados e não mencionados** é que falham
- Justificativa: evidências são derivadas dos artefatos da sprint; ausência ≠ rejeição
- Implementado em `evaluator.py` com comentário de política documentado

Arquivos centrais:
- `src/cvg_harness/evaluator/evaluator.py`

## Critério de aprovação final
Todos os itens abaixo são verdade:
- ✅ `pytest -q` continua verde (269 testes)
- ✅ Artefato final de release unificado (`release-readiness-report.json` + sidecar MD)
- ✅ `0016` e `0018` atualizados para estado final
- ✅ Demo aprova release com métricas coerentes (pass_rate=100%, cost=$50, rounds=0)
- ✅ Política de edge cases formalizada e documentada

## Comandos de validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "release-readiness-report|release-readiness.md|269 testes|PR-07|não está aprovada|blocked" src README.md examples docs tests -g '!**/__pycache__/**'
```

## Veredito
**APROVADA** — Todos os bloqueios resolvidos em 2026-04-16.
- auditoria pós-Sprint 12 registrada em `docs/0034-relatorio-de-auditoria-pos-sprint-12.md`
- auditoria pós-Sprint 18 registrada em `docs/0046-relatorio-de-auditoria-pos-sprint-18.md`
