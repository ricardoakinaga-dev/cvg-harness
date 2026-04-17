# 0064 - Sprint 36 - Políticas configuráveis por projeto

## Objetivo
Permitir que o operador ajuste preferências de handoff externo por `capability` no contexto do projeto, sem reescrever defaults do harness nem esconder a seleção final do adapter.

## Estado de partida
- `dispatch --capability ...` já selecionava adapter por ranking
- defaults do produto já aplicavam policies mínimas (`review` preferindo `manual-review`)
- o gap restante era tornar isso configurável por projeto, com trilha auditável

## Entrega
### Policy file por projeto
Adicionar suporte a `.cvg-harness/adapter-policy.json` com merge seguro sobre os defaults do produto.

### Campos suportados
Por capability:
- `preferred_providers`
- `preferred_adapters`
- `disabled_adapters`
- `prefer_manual`

### Regras operacionais
- `preferred_adapters` aumenta score sem esconder o adapter escolhido
- `disabled_adapters` remove adapters do ranking da capability
- `policy_source` e `active_policy` ficam persistidos em `external-dispatch-plan.json`
- `adapters` e `dispatch` expõem a policy efetiva na saída humana/JSON

## Critérios de saída
- projeto pode sobrescrever a policy default sem quebrar o fallback geral
- a policy efetiva fica visível no ranking e no plano externo
- a seleção continua explícita e auditável
- a suíte continua verde

## Encerramento
Entrega concluída com policies configuráveis por projeto:
- `.cvg-harness/adapter-policy.json` entra no ranking por capability
- `external-dispatch-plan.json` persiste `policy_source` e `active_policy`
- `cvg adapters` e `cvg dispatch` mostram a policy efetiva
- documentação de contratos externos e artefatos foi alinhada

## Validação
- `pytest -q tests/test_operator_cli.py tests/test_runtime.py`
- `pytest -q` → `269 passed`
- `python3 examples/demo_complete_flow.py`
