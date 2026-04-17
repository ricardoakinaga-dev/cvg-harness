# 0049 - Sprint 21 - Execução opt-in e falha externa observável

## Objetivo

Transformar o dispatch externo opt-in em um comportamento observável de produto, com trilha distinta para sucesso e falha, sem quebrar a compatibilidade do fluxo canônico existente.

## Estado de partida

Após a Sprint 20:
- os adapters externos já eram visíveis na UX do operador
- o operador já expunha `inspect` com `known_adapters`
- o comando `cvg adapters` já listava o registry conhecido
- o bridge externo já suportava `dispatch(..., execute=True)` para adapters `cli`

O gap restante era operacional:
- sucesso e falha do dispatch ainda não estavam igualmente visíveis na timeline do operador
- a contagem de sinais externos precisava refletir execução real, não só preparo
- o fluxo legado de avaliação ainda precisava continuar compatível com dummies antigos

## Itens do sprint

### Item 1 — falha externa observável

Quando o dispatch `cli` falhar em modo opt-in, registrar evento de falha externa e persistir o resultado.

Resultado esperado:
- evento `external_execution_failed`
- `external-dispatch-result.json` persistido
- `inspect` expondo o resultado de falha

### Item 2 — sinais externos refletindo sucesso e falha

Manter a métrica canônica coerente quando houver dispatch externo real ou falho.

Resultado esperado:
- `external_execution_signals` conta pedido, planejamento, dispatch e falha
- `external_execution_breakdown` continua disponível no delivery metrics

### Item 3 — compatibilidade com evaluator e orchestrator legados

Aceitar evidência estruturada sem quebrar testes ou dummies antigos que ainda não conhecem o novo contrato.

Resultado esperado:
- `Evaluator` reconhece evidência estruturada sem duplicar o texto achatado
- `FlowOrchestrator` continua funcionando com avaliadores legados

## Critérios de saída

- dispatch `cli` opt-in pode terminar em `dispatched` ou `failed`
- falha externa aparece na timeline do operador
- métricas continuam verdes e com breakdown atualizado
- o fluxo legado de testes continua passando

## Fechamento

Entrega concluída com a execução opt-in e a falha externa observáveis:
- `external_execution_failed` agora entra na timeline do operador
- `external_execution_breakdown` é preservado em métricas canônicas
- `FlowOrchestrator` mantém compatibilidade com avaliadores antigos
- evidência estruturada continua reconhecida sem perder o legado textual

Validação executada nesta rodada:
- `pytest -q` → `225 passed`
