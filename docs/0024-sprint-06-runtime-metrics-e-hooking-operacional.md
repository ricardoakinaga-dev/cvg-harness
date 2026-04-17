# 0024. Sprint 06 - Consolidação operacional de runtime e métricas auxiliares

## Objetivo
Dar um passo curto de maturidade operacional na linha de **runtime + métrica operacional**, sem mudar
semântica de aprovação já aprovada.

O foco é reduzir risco de execução de hooks e estabilizar a evidência contratual dessa camada.

## Estado de partida
- O projeto segue aprovado na trilha `0019`.
- Sprints `0021` e `0023` estão encerradas.
- `RuntimeAutomation` e `RuntimeExecutor` existem e estão cobertos em modo simulado.
- Há pouca evidência contratual explícita para o comportamento com execução real de hooks (falhas, timeout e
  serialização de resultado).
- Não há regressão de arquitetura prevista; o estado atual é de refinamento de observabilidade e contrato operacional.

## Itens do sprint

### 1. Documentar política operacional de execução de hooks
**Status:** `done`

Objetivo:
- registrar no README e, se necessário, em documento central de operações:
  - modo padrão de uso (`simulated=True`);
  - quais flags/condições habilitam execução real;
  - impacto de segurança e rastreabilidade esperado.

Arquivos alvo:
- `README.md`
- `docs/0024-sprint-06-runtime-metrics-e-hooking-operacional.md` (notas de decisão)

Critério de saída:
- leitura pública deixa explícito que execução real é opt-in e rastreável.

### 2. Cobrir caminhos de `RuntimeExecutor` em modo real de forma determinística
**Status:** `done`

Objetivo:
- garantir por teste que `RuntimeExecutor` em modo real devolve status de sucesso/falha de forma previsível
  quando `subprocess.run` falha, retorna código não-zero ou timeout.

Arquivos alvo:
- `tests/test_runtime.py`
- `src/cvg_harness/auto_runtime/runtime_automation.py`

Critério de saída:
- cobertura de regressão para retorno de status `success`, `failed`, `timeout`, `error` sem depender de execução real fora de controle.

### 3. Consolidar roteiro de smoke para fluxo de runtime no roteiro de demos
**Status:** `done`

Objetivo:
- registrar um caminho reprodutível (documentado) para quem usa `RuntimeExecutor` e `FallbackPolicy` em demos,
  sem alterar comportamento de fluxo.

Arquivos alvo:
- `examples/example_fallback_demo.py` (se atualização mínima de comentários/roteiro for necessária)
- `docs/0024-sprint-06-runtime-metrics-e-hooking-operacional.md`

Critério de saída:
- documentação do roteiro contém comandos e expectativa de saída para modo simulado.

### Roteiro de smoke reprodutível (modo simulado)

Execução mínima de contrato (sem efeitos colaterais externos):

```python
from cvg_harness.auto_runtime.runtime_automation import (
    RuntimeAutomation,
    RuntimeExecutor,
    RuntimeHook,
    HookEvent,
)

auto = RuntimeAutomation()
auto.register_hook(
    HookEvent.LINT_TRIGGER,
    RuntimeHook(event="lint_trigger", command="python -m py_compile {artifact}"),
)
executor = RuntimeExecutor(auto, simulated=True)

results = executor.run_hooks(HookEvent.LINT_TRIGGER, {"artifact": "/tmp/demo_example.py"})
print(results)
```

Comando:

```bash
python3 - <<'PY'
from cvg_harness.auto_runtime.runtime_automation import (
    RuntimeAutomation,
    RuntimeExecutor,
    RuntimeHook,
    HookEvent,
)

auto = RuntimeAutomation()
auto.register_hook(
    HookEvent.LINT_TRIGGER,
    RuntimeHook(event="lint_trigger", command="python -m py_compile {artifact}"),
)
executor = RuntimeExecutor(auto, simulated=True)

results = executor.run_hooks(HookEvent.LINT_TRIGGER, {"artifact": "/tmp/demo_example.py"})
print(results)
PY
```

Expectativa de saída:
- `results == [{"hook_event": "lint_trigger", "command": "python -m py_compile /tmp/demo_example.py", "status": "simulated", "reason": "...real para execução real"}]`
- não ocorrerá chamada a `subprocess.run`
- o mesmo trecho é seguro para CI, documentação e revisão manual

Observação: para validar execução real, manter o `RuntimeExecutor` com `simulated=False`, em ambiente de teste controlado.

## Arquivos alvo
- `README.md`
- `src/cvg_harness/auto_runtime/runtime_automation.py`
- `tests/test_runtime.py`
- `examples/example_fallback_demo.py`
- `docs/0024-sprint-06-runtime-metrics-e-hooking-operacional.md`

## Critérios de saída
- Nenhuma mudança de semântica em aprovação/rejeição do fluxo principal.
- Semântica de runtime fica estável e explicitada.
- Novos testes evitam regressão em paths reais de hook execution com retorno controlado.
- Testes e demo continuam sem quebrar aprovação já conquistada.

## Validação
```bash
pytest -q
python3 examples/demo_complete_flow.py
rg -n "RuntimeExecutor|RuntimeAutomation|simulated|simulad|hook|subprocess|0024-sprint-06|done|todo" docs README.md examples tests src/cvg_harness/auto_runtime -g '!**/__pycache__/**'
```

## Critério de encerramento
- Itens 1, 2 e 3 concluídos com evidência textual e testes.
- comportamento de produto central preservado.
- a trilha documental passa para este sprint sem ambiguidade.
- sprint pode ser executada por agente único com leitura em `docs/0016` e `0019`.
- próxima continuidade documental está em `docs/0026-sprint-08-higienizacao-estado-real-e-rastreabilidade-documental.md`.
