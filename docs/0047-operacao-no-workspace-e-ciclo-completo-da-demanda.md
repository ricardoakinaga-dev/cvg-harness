# 0047 — Operação no Workspace e Ciclo Completo da Demanda

## Workspace-aware
Ao abrir `harness`, o produto usa o diretório atual como contexto e trabalha com `.harness/`.

Estrutura persistida esperada:
```text
.harness/
  runs/
  artifacts/
  reports/
  logs/
  ledgers/
  session/
```

## Ciclo resumido
1. Demanda nova em linguagem natural
2. Classificação FAST/ENTERPRISE e seleção de model
3. Execução de governança (research, PRD, SPEC, planning, evaluator, guardian, drift, release readiness)
4. Fase de aprovação/evidência (`approve`, `continue`)
5. Replanejamento ou conclusão
6. Inspeção/entrega com `inspect`/`resumo`

## Retomada e inspeção
- `harness resume` e comando `resume`/`retome` reutilizam a run ativa.
- `inspect` (ou `o que você alterou?`) mostra:
  - run atual
  - artifacts/reports
  - pending action, next_action
  - timeline e estado causal.

## Persistência por run
- `.harness/runs/<run_id>/plan.json`
- `.harness/runs/<run_id>/event-log.jsonl`
- `.harness/runs/<run_id>/progress.json`
- `artifacts/*`, `reports/*`
