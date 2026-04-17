# 0044 - Sprint 18 - CLI canônico de operação

## Objetivo

Evoluir o `cvg-harness` de toolkit modular para CLI-first operational orchestrator, preservando a engine interna existente.

## Escopo desta sprint

1. introduzir comando canônico `cvg run`
2. expor comandos de operação: `status`, `inspect`, `continue`, `pause`, `approve`, `replan`, `events`, `metrics`
3. separar formalmente modo operador e modo avançado no `--help`
4. padronizar workspace operacional em `.cvg-harness/`
5. reposicionar README e documentação para uso real no terminal

## Estado inicial

Antes desta sprint, a CLI expunha majoritariamente primitives granulares (`classify`, `lint`, `guard`, `drift`, `progress`, `event`, `handoff`, `template`).

A engine era forte, mas a UX principal ainda não deixava claro qual era o caminho canônico para conduzir uma demanda até o fim.

## Implementação

### Bloco 1 - Auditoria
- gap confirmado entre engine forte e experiência fragmentada
- README estava toolkit-first
- CLI não tinha entrada principal de alto nível

### Bloco 2 - Modelagem do CLI canônico
- definido modo operador
- definido modo avançado
- definidos estados operacionais e pendências humanas

### Bloco 3 - Implementação
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `src/cvg_harness/flow.py`
- `src/cvg_harness/types.py`
- `tests/test_operator_cli.py`

### Bloco 4 - Documentação
- `README.md`
- `docs/0039-operacao-real-do-cvg-harness.md`
- `docs/0040-design-do-cli-e-contratos-de-comando.md`
- `docs/0041-separacao-entre-engine-e-experiencia-operacional.md`
- `docs/0042-workspace-operacional-e-ciclo-de-vida-da-demanda.md`
- `docs/0043-limites-atuais-e-roadmap-de-terminal-orchestrator.md`

## Critérios de saída

- `cvg run` existe
- `status`, `inspect`, `continue`, `pause`, `approve`, `replan`, `events`, `metrics` existem
- comandos avançados continuam disponíveis
- help mostra modo operador primeiro
- run canônica persiste estado operacional
- README ficou operador-first
- documentação nova descreve o estado real

## Encerramento

Sprint encerrada com os seguintes resultados verificáveis:
- `pytest -q` verde com `217/217` testes
- `examples/demo_complete_flow.py` terminando em `Release: APPROVED`
- CLI operador-first materializada em `run`, `status`, `inspect`, `continue`, `pause`, `approve`, `replan`, `events`, `metrics`
- melhorias incrementais pós-sprint já absorvidas: `inspect` causal, evidência estruturada e contratos de executor externo

Auditoria consolidada em `docs/0046-relatorio-de-auditoria-pos-sprint-18.md`.
Próxima rodada incremental aberta em `docs/0047-sprint-19-executor-externo-e-evidencia-operacional.md`.
