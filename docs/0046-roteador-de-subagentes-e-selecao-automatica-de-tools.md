# 0046 — Roteador de Subagentes e Seleção Automática de Tools

## Objetivo

Decidir automaticamente o plano operacional com base em:

- intenção da mensagem do usuário,
- estado da run,
- classificação de risco (`FAST`/`ENTERPRISE`),
- contexto atual da sessão.

## Subagentes/capas internos contemplados

- classifier
- research
- prd
- spec_builder
- spec_linter
- sprint_planner
- evaluator
- architecture_guardian
- drift_detector
- release_readiness
- replan_coordinator
- metrics_aggregator

## Decisão atual (heurística inicial)

- Mensagem de demanda nova: abre `start_run` com modo sugerido via `calculate_mode`.
- Mensagem de aprovação (`aprovar`, `sim`, `ok`): aciona `approve`.
- `status`/`inspect`/`resume`: chamada direta de consulta.
- `continue`: resume run via `OperatorService.continue`.
- `replaneje`: aciona `replan`.
- Perguntas explicativas: `inspect + causal`.

## Seleção de modelos

- `ModelProvider` resolve provider e modelo em configuração e checa suporte.
- MiniMax é o padrão sugerido.
- OpenAI / OpenRouter disponíveis para fallback por configuração.
