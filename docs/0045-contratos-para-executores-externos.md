# 0045 - Contratos para executores externos

## Objetivo

Formalizar a integração com executores externos sem quebrar a separação entre:
- harness como orquestrador
- executor como agente externo, hook ou sistema delegado

## Contratos implementados

O código agora possui contratos explícitos em:
- `src/cvg_harness/auto_runtime/external_executor.py`

Tipos principais:
- `ExternalExecutorAdapter`
- `ExecutionDispatchRequest`
- `ExecutionDispatchResult`
- `ExternalExecutorRegistry`
- `ExternalExecutorBridge`

## Papel de cada contrato

### `ExternalExecutorAdapter`
Descreve um executor externo conhecido.

Campos principais:
- `name`
- `transport`: `manual`, `cli` ou `webhook`
- `entrypoint`
- `capabilities`
- `emits_evidence`
- `requires_human_approval`
- `provider`
- `context_hints`
- `required_context`
- `example_contexts`
- `command_examples`

### `ExecutionDispatchRequest`
É o payload que o harness entrega para um executor externo.

Campos principais:
- `run_id`
- `sprint_id`
- `demand`
- `objective`
- `workspace`
- `changed_files`
- `evidence_targets`
- `context`
- `context_sources`
- `metadata`

### `ExecutionDispatchResult`
É o retorno formal do bridge.

Estados principais:
- `planned`
- `manual_required`
- `dispatched`
- `failed`

## Regra arquitetural

O harness não faz dispatch externo por padrão.

Ele pode:
- registrar adapters
- preparar requests
- planejar um dispatch
- disparar explicitamente adapters `cli` quando isso for opt-in

Na trilha operacional atual, o modo operador também persiste um sidecar
`external-dispatch-plan.json` na run para deixar explícito o hand-off
sem tratar isso como execução automática.

Ele não assume automaticamente que:
- todo executor é seguro
- todo executor deve rodar sem aprovação humana
- todo executor devolve evidência utilizável

## Por que isso importa

Sem contrato formal, integração externa vira acoplamento ad hoc.

Com contrato formal:
- o loop de governança continua estável
- a CLI continua honesta sobre seus limites
- o produto pode crescer para execução real sem virar executor por acidente

## Limite atual

O `ExternalExecutorBridge` ainda é uma ponte deliberadamente contida:
- `manual` e `webhook` ficam como planejamento/hand-off explícito
- `cli` pode ser disparado apenas quando `execute=True`
- o contrato existe antes da automação plena

Esse desenho é intencional.

## Adapters padrão atuais

O registry default agora já nasce com adapters operacionais suficientes para demonstração e handoff assistido:
- `manual-review`: handoff humano genérico
- `local-cli`: adapter local mínimo para dispatch explícito
- `github-actions-review`: adapter CLI provider-aware para contexto vindo de GitHub Actions
- `gitlab-ci-review`: adapter CLI provider-aware para contexto vindo de GitLab CI

Esses adapters não transformam o harness no executor final. Eles só tornam o handoff mais explícito, observável e próximo do contexto real.

## Seleção por capability no operador

O modo operador agora pode orientar a escolha do adapter por capability, sem esconder o executor real.

Na prática:
- `cvg adapters --capability ci` ranqueia adapters compatíveis usando o contexto atual da run
- `cvg dispatch --capability ci` auto-seleciona o adapter mais adequado
- a seleção continua explícita e auditável via `selection_reason` e `suitability_score`

Isso reduz atrito operacional, mas não transforma o harness em executor automático.

As policies atuais já começam a refletir intenção operacional:
- `review` prefere `manual-review` por padrão
- `ci` continua priorizando adapters compatíveis com o provider observado no runtime/CI
- `selection_reason` e `suitability_score` deixam esse critério explícito para auditoria


## Policies configuráveis por projeto

A seleção por capability agora também pode ser ajustada por projeto em `.cvg-harness/adapter-policy.json`, sem remover os defaults seguros do produto.

Campos suportados por capability:
- `preferred_providers`
- `preferred_adapters`
- `disabled_adapters`
- `prefer_manual`

Regras:
- o merge é aditivo sobre os defaults do harness
- `disabled_adapters` remove adapters do ranking para aquela capability
- `preferred_adapters` ajusta o score sem esconder o adapter final escolhido
- o plano externo persiste `policy_source` e `active_policy` para auditoria

Exemplo:

```json
{
  "capabilities": {
    "review": {
      "preferred_adapters": ["github-actions-review"],
      "disabled_adapters": ["manual-review"],
      "prefer_manual": false
    }
  }
}
```
