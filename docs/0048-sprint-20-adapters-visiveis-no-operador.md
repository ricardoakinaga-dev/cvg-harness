# 0048 - Sprint 20 - Adapters visíveis no operador

## Objetivo

Expor os executores externos conhecidos como superfície operacional do modo operador, sem quebrar a separação entre harness e executor.

## Estado de partida

Após a Sprint 19:
- o hand-off explícito para executor externo já existia
- `inspect` já mostrava o plano de dispatch
- o evaluator já reconhecia evidência estruturada parcial
- métricas já contavam sinais de execução externa

O gap restante era de UX operacional: os adapters existiam como contrato, mas ainda não apareciam claramente como catálogo do operador.

## Item do sprint

### Item único — adapters visíveis na UX principal

Expor os adapters registrados no registry do harness para inspeção e consulta direta.

Resultado esperado:
- `inspect` passa a mostrar os adapters conhecidos
- existe comando explícito para listar adapters externos
- a descoberta de executores deixa de depender só de leitura de arquivo interno

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `tests/test_operator_cli.py`

## Critérios de saída

- adapters registrados aparecem em `inspect`
- existe comando `cvg adapters`
- a UX continua operator-first
- o runtime e o contrato de dispatch não mudam de forma incompatível

## Fechamento

Entrega concluída com a superfície de adapters exposta no operador:
- `inspect` mostra `known_adapters`
- `cvg adapters` lista `manual-review` e `local-cli`
- a trilha operacional segue estável e sem automação cega

Validação executada nesta rodada:
- `pytest -q` → `221 passed`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0049-sprint-21-relatorio-avaliacao-canonicidade.md`
