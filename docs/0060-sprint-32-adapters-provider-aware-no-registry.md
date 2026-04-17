# 0060 - Sprint 32 - Adapters provider-aware no registry

## Objetivo

Consolidar o registry de executores externos com adapters padrão mais reais por provider e tornar a seleção no modo operador mais informativa, sem quebrar a separação entre harness e executor.

## Estado de partida

Após a Sprint 31:
- `dispatch` já era provider-aware
- `external-dispatch-plan.json` já persistia contexto, fontes e lacunas
- o gap restante estava no registry: os adapters default ainda eram poucos e o operador não via claramente provider, contexto mínimo e exemplos de comando
- além disso, workspaces antigos com `executors.json` já persistido não recebiam automaticamente adapters novos

## Item único

### Registry default enriquecido + merge não destrutivo

Adicionar adapters padrão mais próximos de providers reais e garantir que o carregamento do registry faça merge dos defaults novos sem sobrescrever customizações locais.

Resultado esperado:
- registry default inclui `github-actions-review` e `gitlab-ci-review`
- `cvg adapters` mostra `provider`, `required_context`, `context_hints` e `command_examples`
- `dispatch` pode usar esses adapters diretamente com contexto derivado de runtime/CI
- `executors.json` legado recebe adapters novos por merge não destrutivo
- o harness continua orquestrador; adapters seguem explícitos e opt-in

Arquivos-alvo:
- `src/cvg_harness/auto_runtime/external_executor.py`
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/cli/cli.py`
- `tests/test_operator_cli.py`
- `tests/test_runtime.py`
- `docs/0045-contratos-para-executores-externos.md`
- `README.md`

## Critérios de saída

- o operador enxerga adapters provider-aware no registry padrão
- workspaces antigos continuam compatíveis e recebem novos defaults
- `dispatch` usa adapters provider-aware reais no caminho feliz
- a suíte permanece verde

## Fechamento

Entrega concluída com adapters provider-aware no registry:
- o registry default passou a incluir `github-actions-review` e `gitlab-ci-review`
- `cvg adapters` agora mostra provider, contexto mínimo, hints e exemplos de comando
- o carregamento do `executors.json` faz merge não destrutivo dos defaults novos
- `dispatch` já consegue usar adapters provider-aware reais com contexto derivado de `runtime-hooks.json` e `ci-result.json`

Validação executada nesta rodada:
- `pytest -q tests/test_operator_cli.py tests/test_runtime.py` → `61 passed`
- `pytest -q` → `264 passed`
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`
- `python3 -m cvg_harness adapters` → adapters provider-aware visíveis

Encadeamento:
- próximo ciclo incremental deve tratar seleção/orientação de adapter por capability no operador, ou enriquecer o handoff externo com políticas por capability sem transformar o harness em executor final
