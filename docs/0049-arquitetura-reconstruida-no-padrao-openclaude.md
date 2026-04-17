# 0049 — Arquitetura Reconstruída no Padrão OpenClaude

## Padrões adotados
- ponto único de entrada: `harness`
- onboarding guiado inicial
- loop conversacional persistido
- separação clara entre UX e core de execução
- subagentes e ferramentas internos encapsulados
- configuração por camadas (flags -> env -> projeto -> global)

## O que foi preservado
- núcleo de governação já existente (`classification`, `research`, `prd`, `spec_builder`, `linter`, `sprint`, `evaluator`, `guard`, `drift`, `release`, `metrics`, `replan`, `ledger`).
- integração com adapters de execução externa e runtime.

## O que foi adaptado para identidade própria
- mensagem e vocabulário do produto direcionado ao usuário final
- fluxo de comandos principal em português (não técnico)
- `harness` como cara do produto, com `cvg`/`debug` no modo avançado.

## Estrutura-alvo (resumida)
```text
src/
  app/         # front-agent, sessão, UX de terminal
  routing/     # intenção -> ação; engine route
  providers/   # minimax/openai/openrouter
  workspace/   # detecção e estrutura local
  runtime/     # execuções e integrações
  operator/    # orchestrador de gates e política
  tools/       # toolkit técnico (file/system/shell/planning/subagent/context)
  session/
```

## Caminho para headless
A separação atual já permite extrair `operator` + `session` + `routing` para API local no futuro, com o front de terminal reutilizando a mesma orquestração.
