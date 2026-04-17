# 0044 — Agente de Terminal Prompt-First

`harness` é o modo principal do projeto: o usuário abre o comando e fala em linguagem natural.

## O que mudou
- entrada principal agora é apenas:
```bash
harness
```
- não é necessário executar `classify`, `lint`, `guard`, `drift` manualmente.

## Fluxo principal
1. `harness` inicia o agente.
2. Detecta workspace atual (`cwd`) e carrega configuração.
3. Executa onboarding se não houver configuração válida.
4. Entra em loop conversacional:
   - nova demanda (`criar módulo de permissões`)
   - inspeção de estado (`status`, `inspect`, `o que você alterou?`)
   - controle (`continue`, `approve`, `replaneje`, `resumo`)

## Exemplos de diálogo
- `> criar módulo de permissões por setor`
- `> revisar este projeto e montar um plano seguro para modularizar a agenda`
- `> adicionar autenticação OAuth2 com Google`
- `> status`
- `> continue`
- `> replaneje com menos risco`
- `> por que você escolheu enterprise?`
- `> retome`
- `> sair`

## Separação de responsabilidade
- `app/agent.py`: UX, loop, roteamento de intenção.
- `routing/`: decide ação da rodada (`status`, `inspect`, `resume`, `replan` etc.).
- `operator/` + módulos de governance (`classification`, `research`, `prd`, `spec_builder`, `linter`, `sprint`, `evaluator`, `guardian`, `drift`, `release`, `fallback`, `metrics`): execução real do motor.
- `session/`: estado da sessão e memória local.

## Comportamentos expostos ao usuário
- `status`: situação da run ativa.
- `inspect`: artefatos + evidências + próxima ação.
- `history`: histórico da sessão.
- `resume`: retoma da run ativa.
- `debug ...`: namespace técnico não exposto por padrão.

## Resultado final esperado
Ao concluir uma demanda de sucesso, o agente retorna um resumo com:
- modo escolhido (FAST/ENTERPRISE), run_id,
- gates/sprints executados,
- decisões críticas (evaluator, drift, release),
- artefatos e relatórios gerados.
