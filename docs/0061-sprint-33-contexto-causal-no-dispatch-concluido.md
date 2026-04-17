# 0061 - Sprint 33 - Contexto causal no dispatch concluido

## Objetivo

Consolidar o dispatch externo como uma trilha causal completa, com o plano e o resultado carregando proveniência de runtime/provider de forma consistente.

## Estado de partida

Após as Sprints 31 e 32:
- `external-dispatch-plan.json` já carrega `provider`, `context_sources`, `required_context`, `missing_required_context`, `available_context_keys`, `runtime_profile` e `runtime_provider`
- `external-dispatch-result.json` já carrega `runtime_profile`, `runtime_provider` e `context_sources`
- `inspect` já expõe o bloco causal de dispatch com plan/result
- o dispatch continua opt-in e controlado pelo operador

O gap restante era mais de consolidação documental do que de engine:
- a trilha precisava de um fechamento único e explícito
- os docs intermediários já refletiam a implementação, mas ainda pareciam etapas separadas

## Item único

### Fechamento causal do dispatch externo

Documentar a trilha concluída do dispatch provider-aware, com plano e resultado espelhando o mesmo contexto causal.

Resultado esperado:
- plano e resultado externos compartilham runtime/provider/contexto causal
- `inspect` mostra a mesma origem de contexto nas duas faces do dispatch
- o contrato dos sidecars continua estável
- a trilha deixa de parecer fragmentada entre 0059/0060

Arquivos-alvo:
- `src/cvg_harness/operator/service.py`
- `src/cvg_harness/contracts/artifact_contracts.py`
- `tests/test_operator_cli.py`
- `docs/0059-sprint-31-contexto-provider-aware-em-dispatch.md`
- `docs/0060-sprint-32-proveniencia-no-resultado-externo.md`
- `docs/INDEX.md`

## Critérios de saída

- o dispatch provider-aware fica documentado como fluxo concluído
- a provenance do runtime aparece tanto no plano quanto no resultado
- a navegação documental deixa claro qual doc é histórico e qual é o fechamento
- a suíte permanece verde

## Fechamento

Entrega concluída com contexto causal no dispatch:
- `external-dispatch-plan.json` e `external-dispatch-result.json` compartilham a proveniência operacional derivada do runtime
- `inspect` expõe o fluxo causal completo do dispatch
- os docs intermediários foram mantidos como histórico e o fechamento foi consolidado aqui

Validação executada nesta rodada:
- `pytest -q` -> `261 passed`
- `python3 examples/demo_complete_flow.py` -> `Fluxo: completed`, `Release: APPROVED`

Encadeamento:
- próximo ciclo incremental aberto em `docs/0062-sprint-34-inspecao-humana-do-dispatch-concluido.md`
