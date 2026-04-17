# 0022. Sprint 04 - Melhoria de documentação operacional de exemplos e demonstração

## Objetivo
Manter a entrega estável com melhor legibilidade operacional para quem usa demo e exemplos,
sem alterar fluxo funcional.

## Estado de partida
- Aprovação de Sprint 02 preservada.
- Sprint 03 e 0021 já encerradas com escopo de rastreabilidade e catálogo de eventos.
- Estado atual real confirmado:
  - `pytest -q` passa.
  - `examples/demo_complete_flow.py` executa fluxo canônico.
  - Há ruído residual em material de consumo humano (contagem de testes, contexto de PRs e
    comunicação de cenário canônico/sintético nos exemplos).

## Limite de escopo (incremento)
- Não reabrir decisões estruturais de arquitetura, contratos centrais ou aprovação do projeto.
- Não alterar comportamento de fluxo/gates/artefatos canônicos.
- Foco exclusivo em comunicação operacional dos exemplos e trilha de leitura.

## Itens do sprint

### 1. Corrigir trilha de status pública no README
**Status:** `done`

Objetivo:
- Alinhar o resumo público ao estado atual sem abrir escopo funcional.

Arquivo(s) alvo:
- `README.md`

Entregáveis:
- número de testes atualizado para o valor real da suíte;
- referência de PRs/sprint em linguagem consistente com aprovação já alcançada;
- mensagem curta para distinguir artefatos canônicos x materiais de apoio em leitura humana.

Critério de saída:
- não há claim central contradizendo estado real (ex.: quantidade de testes/sprints fora do real).

### 2. Revisar o `demo_complete_flow.py` para clareza de modo de evidência
**Status:** `done`

Objetivo:
- tornar explícito no arquivo e sua saída textual a fronteira entre:
  - fluxo canônico executado pelo `FlowOrchestrator`;
  - evidência descritiva/sintética usada para apresentação.

Arquivo(s) alvo:
- `examples/demo_complete_flow.py`

Entregáveis:
- comentário/cabeçalho curto sobre natureza dos exemplos;
- seção de saída final com texto padrão de leitura (fluxo canônico vs artefatos auxiliares).

Critério de saída:
- leitor entenda rapidamente que o demo demonstra o fluxo real, e que parte do texto pode ser didático.

### 3. Preparar roteiro de fallback/contradição para exemplo futuro
**Status:** `done`

Objetivo:
- deixar o próximo sprint com backlog executável sobre cenário de falha/replanejamento sem mexer no fluxo atual.

Arquivo(s) alvo:
- `examples/example_fallback_demo.py`
- `docs/0022-sprint-04-melhoria-de-demo-e-exemplos.md`

Entregáveis:
- plano de atualização/adição de exemplo que cubra:
  - aprovação de sprint com `next_action` vazio;
  - mensagem de `next_action` de fallback;
  - rejeição por `release` quando aplicável.
- implementado no novo arquivo de exemplo com roteiro de 3 cenários executável.

Critério de saída:
- sprint deixa explicitado um caminho de execução de cenários não-felizes reutilizável no próximo ciclo.

## Arquivos alvo
- `README.md`
- `examples/demo_complete_flow.py`
- `examples/example_fallback_demo.py`
- `docs/0019-checklist-final-de-aprovacao.md`
- `docs/0020-sprint-03-consolidacao-documental.md`
- `docs/0022-sprint-04-melhoria-de-demo-e-exemplos.md`

## Critérios de saída
- Não há alteração funcional fora de artefatos de comunicação operacional.
- README e exemplos apresentam estado atual com precisão e distinção do canônico.
- trilha documental passa a apontar para este novo sprint.

### Encerramento do sprint
- 3 itens do sprint concluídos (1 a 3).

## Validação
```bash
python3 examples/example_fallback_demo.py
python3 examples/demo_complete_flow.py
pytest -q
rg -n "Sprint 04|Sprint 03|APROVADA|release-readiness-report.json|release-readiness\\.md|161 testes|demos|fallback" docs README.md examples tests -g '!**/__pycache__/**'
```

## Critério de encerramento
- critérios dos itens 1, 2 e 3 concluídos;
- nenhum novo comportamento funcional foi introduzido;
- trilha documental principal aponta para este documento como continuação operacional.

## Continuidade
- A etapa seguinte está documentada em `docs/0023-sprint-05-higienizacao-de-documentacao-residual.md`.
