# 0047 — Operação no Workspace e Ciclo da Demanda

## Workspace-aware

O agente opera sempre no diretório atual, sem precisar informar project path.

Estrutura persistente padrão:

- `.harness/`
- `.harness/runs/`
- `.harness/artifacts/`
- `.harness/reports/`
- `.harness/logs/`
- `.harness/ledgers/`
- `.harness/session/`

## Ciclo de demanda

1. Usuário envia demanda em linguagem natural.
2. Router calcula intenção e modo (`FAST`/`ENTERPRISE`).
3. Engine executa fases (research, PRD, SPEC, lint, sprint planner, guard, drift, evaluator, release).
4. Sessão fica com `run_id` persistido em `.harness/session/current.json`.
5. Comandos da sessão:
   - `status`
   - `continue`
   - `inspect`
   - `retome`
   - `replaneje`

## Retomada

- `harness resume` retorna estado da run ativa em `.harness/current-run.txt` e `.harness/session/current.json`.
- O usuário pode retomar no mesmo workspace sem perder histórico da conversa.
