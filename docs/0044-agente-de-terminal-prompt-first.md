# 0044 — Agente de Terminal Prompt-First

`harness` é o modo principal de operação.  
O usuário fala em linguagem natural e o agente transforma intenção em fluxo interno.

## Visão do modo principal

- Entrada principal: `harness`
- Entrada interativa: prompt livre
- Resultado: resposta com estado, decisão e próximo passo

### Fluxo esperado

1. O usuário inicia em qualquer diretório de projeto.
2. O agente detecta workspace atual (`cwd`) e carrega estado `.harness`.
3. Valida configuração (onboarding se necessário).
4. Entra em loop conversacional.
5. Router decide o plano de execução e chama módulos de governança.
6. Entrega retorno no mesmo terminal, em português, sem exigir comandos técnicos.

Exemplos:

- `harness`
- `> criar módulo de permissões por setor`
- `> revisar este projeto e montar um plano seguro para modularizar a agenda`
- `> adicionar autenticação OAuth2 com Google`
- `> status`
- `> continue`
- `> retome`
- `> o que você alterou?`
- `> por que você escolheu enterprise?`

## Loop conversacional real

O front-agent mantém:

- estado da sessão (`session/current.json`)
- histórico linear de turns (`session/history.jsonl`)
- run ativa (`OperatorService.get_current_run_id`)

### Rotas de interação implementadas

| Rota | Entrada natural | Comportamento |
|---|---|---|
| nova demanda | texto de tarefa | abre nova run, classifica FAST/ENTERPRISE e seleciona modelo |
| status | `status` | consulta `OperatorService.status` |
| inspect | `inspect`, `o que você alterou?` | resume dados + artefatos |
| resume | `resume`, `retome` | recarrega run ativa |
| continue | `continue`, `aprovar` | chama `continue_run` com evidências/arquivos se houver |
| replan | `replaneje` | aciona `replan` e retorna ação |
| reason | `por que` + contexto de decisão | retorna classificação/score |
| config | `config` | relança onboarding |
| doctor | `doctor`/`health` | checagens de ambiente e provider |
| debug | `debug ...` | encaminha para namespace técnico |

As rotas estão em [`src/cvg_harness/routing/router.py`]( /home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/routing/router.py )  
e o dispatcher está em [`src/cvg_harness/app/agent.py`]( /home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/app/agent.py ).

## Separação UX vs engine

- UX (`app/`) conversa e orquestra.
- Engine (`operator/`, `classification/`, `research/`, `prd/`, `spec_builder/`, `linter/`, `sprint/`, `evaluator/`, `guardian/`, `drift/`, `release/`, `ledger/`, `fallback/`, `metrics/`) executa a governança existente.

## Modo técnico (oculto no produto principal)

O namespace técnico sobrevive para engenharia:

- `harness debug ...`
- também há CLI técnico legado `cvg <comando>`.

Ele é mantido para scripts, validações e operações diretas sem quebrar backward compatibility.

## Resultado esperado da interação

Ao final de uma demanda concluída, o agente pode retornar:

- `Run`, `Modelo`, `Status` e `Pendência`
- resumo dos gates avaliados
- artefatos e evidências associadas
- mensagem de conclusão com próximo passo.
