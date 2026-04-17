# 0023. Sprint 05 - Higienização residual da trilha documental

## Objetivo
Fechar resíduos leves restantes de rastreabilidade documental sem alterar
comportamento de produto, mantendo o estado aprovado e a trilha histórica
consolidada.

## Estado de partida
- Entrega aprovada em [0019](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0019-checklist-final-de-aprovacao.md).
- Sprint 03, 0021 e 0022 concluídas.
- O projeto segue estável:
  - `pytest -q` verde;
  - `examples/demo_complete_flow.py` executa fluxo canônico;
  - 161 testes.
- Há ruído residual de manutenção de trilha em documentos de fechamento.

## Limite de escopo (incremento)
- Não tocar fluxo funcional, contratos centrais, gates, artefatos canônicos ou
  módulos de runtime.
- Não reabrir decisão de aprovação já aprovada.
- Somente precisão textual, encadeamento documental e validação de rastreabilidade.

## Itens do sprint

### 1. Corrigir inconsistência residual de estado na trilha final
**Status:** `done`

Objetivo:
- Padronizar referência final da aprovação para o estado atual real (sem número de testes obsoleto).

Arquivos alvo:
- [docs/0019-checklist-final-de-aprovacao.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0019-checklist-final-de-aprovacao.md)

Entregáveis:
- Atualizar contagem numérica final para `161 testes`.
- Confirmar que `APROVADA` aparece apenas como veredito consolidado.

Critério de saída:
- leitura do veredito final sem ambiguidade histórica recente.

### 2. Encadear o backlog para o próximo ciclo operacional
**Status:** `done`

Objetivo:
- Atualizar o ponteiro de continuidade dos docs que ainda apontam para `0022` como próximo ciclo.

Arquivos alvo:
- [docs/0016-backlog-executavel-de-correcao.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0016-backlog-executavel-de-correcao.md)
- [docs/0022-sprint-04-melhoria-de-demo-e-exemplos.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0022-sprint-04-melhoria-de-demo-e-exemplos.md)

Entregáveis:
- troca explícita do próximo ciclo para `docs/0023-sprint-05-higienizacao-de-documentacao-residual.md` onde aplicável.

Critério de saída:
- trilha de documentação não retorna a sprint já encerrada como próximo ciclo.

### 3. Tornar validação documental de status rastreável
**Status:** `done`

Objetivo:
- Consolidar no próprio sprint quais comandos de rastreabilidade devem ser usados para revisar o estado de aprovação e continuidade.

Arquivos alvo:
- [docs/0023-sprint-05-higienizacao-de-documentacao-residual.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0023-sprint-05-higienizacao-de-documentacao-residual.md)

Entregáveis:
- seção de validação com comandos mínimos já alinhados aos padrões já existentes.

Critério de saída:
- execução dos comandos consegue comprovar a continuidade documental sem alterar código.

## Arquivos alvo
- `docs/0016-backlog-executavel-de-correcao.md`
- `docs/0019-checklist-final-de-aprovacao.md`
- `docs/0022-sprint-04-melhoria-de-demo-e-exemplos.md`
- `docs/0023-sprint-05-higienizacao-de-documentacao-residual.md`

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "Sprint 03|Sprint 02|Sprint 04|APROVADA|done|todo|0022-sprint-04|0023-sprint-05|160 testes|161 testes|próximo ciclo" docs README.md examples tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- 3 itens concluídos (`done`) e validações executadas sem reabrir aprovação.
- nenhum comportamento funcional alterado.
- trilha documental passa a apontar claramente o próximo ciclo para `0024`.
