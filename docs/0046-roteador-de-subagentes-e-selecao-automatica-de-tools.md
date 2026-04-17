# 0046 — Roteador de Subagentes e Seleção Automática de Tools

## Objetivo

Decidir, em uma só entrada textual, o fluxo operacional interno sem exigir que o usuário escolha comandos de pipeline.

## Camada de roteamento atual

1. Entrada livre chega em `FrontAgent.start()`.
2. `_run` chama [`route_request`]( /home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/routing/router.py ).
3. `RouteType` seleciona ação:
   - nova demanda, status, inspect, continue, resume, replan, reason, config, doctor, debug, help, exit.
4. Dispatcher (`FrontAgent._dispatch`) chama módulos técnicos apropriados.

## Seleção de subagentes internos

O fluxo de `nova demanda` aciona serviços da engine preservada:

- `classification` (`calculate_mode`)
- `research` (na sequência de execução)
- `prd`
- `spec_builder`
- `spec_linter`
- `sprint_planner`
- `architecture_guardian`
- `drift_detector`
- `evaluator`
- `release readiness`
- `replan_coordinator`
- `metrics_aggregator`

Não há acionamento manual de cada etapa no prompt principal; as chamadas são encadeadas no `OperatorService`.

## Seleção de modelo por modo

Modelo automático atual:

- Modo `FAST` → primeiro modelo `*highspeed` disponível do provider.
- Modo `ENTERPRISE` → primeiro modelo sem `highspeed`.
- Se não houver correspondência, usa `config.default_model`.

Definição em [`_select_model`]( /home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/app/agent.py ).

## Seleção de provider

- provider/credentials vêm da configuração resolvida (`load_config`).
- `minimax` é o default sugerido.
- OpenAI/OpenRouter só entram por configuração explícita ou variável de ambiente.
- `Provider` é construído com `build_provider(...)` sem acoplamento de domínio.

## Quando o agente pede confirmação humana

Condições atuais:

- sprint pendente de aprovação (`approve_sprint`)
- run exigindo bloqueio de segurança (`pending_human_action`)
- replanejamento com decisão de risco alto
- health check/diálogo de explicação solicitado pelo usuário

## Quando bloquear

Bloqueia operação em:

- onboarding incompleto em modo não-interativo
- falhas de configuração crítica de chave
- necessidade de input manual em fluxo técnico (dependente de execução real)
