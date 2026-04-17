# 0016. Backlog executável de correção

## Objetivo
Transformar a auditoria em uma sequência de entregas pequenas, verificáveis e integráveis, alinhadas com a documentação já definida em `docs/`.

## Regra de execução
- não abrir frentes P2/P3 enquanto P0/P1 estrutural estiver inconsistente
- cada PR deve deixar testes passando
- cada PR deve reduzir divergência entre documentação, contratos e código
- nenhuma PR deve aumentar o número de formatos conflitantes de artefato

## Ordem de implementação
1. PR-01 — unificação de schemas e contratos — `done`
2. PR-02 — artefatos canônicos e geração consistente — `done`
3. PR-03 — fluxo fim a fim no orchestrator — `done`
4. PR-04 — gates, fallback e integração operacional — `done`
5. PR-05 — arquitetura, drift e evaluator sem placeholders críticos — `done`
6. PR-06 — release, métricas e readiness de runtime — `done`
7. PR-07 — limpeza de claims, examples e documentação pública — `done`

## PR-01 — Unificação de schemas e contratos
**Status:** `done`

### Entregas
- `done` schema canônico para `classification.json`
- `done` nomes de campos alinhados entre código e contratos
- `done` `GateResult` consistente com os consumidores
- `done` helper único para estados de gate e campos obrigatórios

### Critérios de aceite
- `done` `classification.json` produzido passa na validação contratual
- `done` `evaluate_gate("GATE_0", ...)` funciona com o artefato realmente gerado
- `done` nenhum campo obrigatório do contrato depende de tradução manual de nome
- `done` testes cobrindo compatibilidade entre producer + contract + gate

### Risco que elimina
- falso positivo de conformidade
- gates aprovando ou reprovando com schema errado

## PR-02 — Artefatos canônicos e geração consistente
**Status:** `done`

### Objetivo
Definir formato oficial dos artefatos e fazer todos os agentes produzirem esse formato de forma coerente.

### Decisão recomendada
- usar JSON para contratos e estado operacional
- usar Markdown para artefatos legíveis por humano
- quando houver versão dupla, gerar ambos explicitamente e manter sincronismo

### Escopo
- [src/cvg_harness/research/research_agent.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/research/research_agent.py:17)
- [src/cvg_harness/prd/prd_agent.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/prd/prd_agent.py:17)
- [src/cvg_harness/spec_builder/spec_builder.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/spec_builder/spec_builder.py:17)
- [src/cvg_harness/templates/revised_templates.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/templates/revised_templates.py:130)
- [src/cvg_harness/contracts/artifact_contracts.py](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/contracts/artifact_contracts.py:89)

### Entregas
- `done` `research-notes.md` e `system-map.md` reais
- `done` `prd.md` real
- `done` `spec.md` e `spec.json` gerados juntos
- `done` versionamento e `change_reason` aplicados aos artefatos mutáveis
- `done` validação mais forte de campos mínimos

### Critérios de aceite
- `done` nomes e extensões batem com [0007](</home/ricardo/.openclaw/workspace/cvg-harness/docs/0007-contratos-dos-artefatos.md:14>)
- `done` agentes não salvam `.md` como JSON serializado
- `done` `spec.md` e `spec.json` compartilham `version`
- `done` testes cobrindo persistência e carregamento dos artefatos centrais

### Risco que elimina
- contrato documental sem correspondência no repositório
- drift estrutural logo na geração dos artefatos

## PR-03 — Fluxo fim a fim no orchestrator
**Status:** `done`

### Objetivo
Fazer o `FlowOrchestrator` coordenar o fluxo descrito na documentação, em vez de só persistir estado parcial.

### Entregas
- `done` métodos explícitos para `research`, `prd`, `build_spec`, `plan_sprints`, `evaluate`, `release`
- `done` criação e consumo de handoffs por etapa
- `done` `progress.json` sincronizado ao longo do fluxo
- `done` eventos mínimos obrigatórios registrados no `event-log.jsonl`

### Critérios de aceite
- `done` fluxo FAST mínimo executa até avaliação sem escrever artefatos fora do contrato
- `done` mudança de gate gera evento correspondente
- `done` uma sprint ativa por fluxo é regra enforced, não convenção
- `done` `tests/test_integration.py` cobre um fluxo real com artefatos intermediários

## PR-04 — Gates, fallback e integração operacional
**Status:** `done`

### Objetivo
Conectar gates e fallback ao fluxo real para que bloqueios e replanejamento não sejam peças soltas.

### Entregas
- `done` avaliação real de `GATE_0` a `GATE_9` com critérios compatíveis com os artefatos
- `done` fallback emitindo eventos operacionais
- `done` `ReplanCoordinator` acionado automaticamente em cenários previstos
- `done` suporte coerente a `waived`

### Critérios de aceite
- `done` reprovação do linter impede execução
- `done` falha 1, 2 e 3 do evaluator mudam `next_action` e evento emitido
- `done` misclassification gera `replan_requested`
- `done` testes cobrindo transições relevantes e bloqueios

## PR-05 — Guardian, drift e evaluator sem placeholders críticos
**Status:** `done`

### Objetivo
Substituir stubs dos mecanismos de controle por checagens reais e minimamente confiáveis.

### Entregas
- `done` `ArchitectureGuardian` checando boundary autorizado, alteração fora da zona autorizada e casos mínimos de dependência indevida
- `done` `DriftDetector` cobrindo todas as camadas declaradas em [0011](</home/ricardo/.openclaw/workspace/cvg-harness/docs/0011-spec-lint-architecture-guard-drift-detector.md:48>)
- `done` `Evaluator` validando critérios, evidências, edge cases e contratos esperados por sprint

### Critérios de aceite
- `done` não existir `pass` em verificações centrais que a documentação marca como regra mínima
- `done` avaliação falha quando evidência obrigatória não existe de fato
- `done` drift entre `execution x evaluation` e `evaluation x release readiness` é detectável
- `done` testes novos para cenários negativos, não só happy path

## PR-06 — Release, métricas e readiness de runtime
**Status:** `done`

### Objetivo
Consolidar saída final, métricas e interface com execução externa sem prometer automação inexistente.

### Entregas
- `done` `release-readiness-report.json` como canônico, sidecar MD opcional documentado
- `done` consolidação correta de gates, exceções, riscos residuais e waivers
- `done` métricas calculadas a partir de eventos reais com base $50 para fluxo aprovado
- `done` hooks externos com modo `simulated` testado e contrato explícito

### Critérios de aceite
- `done` release readiness consome `GateResult` sem mismatch de nomes
- `done` métricas não inferem custo/lead time de forma arbitrária (base $50 para fluxo aprovado)
- `done` resultado externo pode ser referenciado por caminho ou ID
- `done` falha de hook relevante entra em evento/gate

## PR-07 — Limpeza de README, exemplos e claims públicas
**Status:** `done`

### Objetivo
Fazer a comunicação pública refletir o estado real do projeto.

### Entregas
- `done` README alinhado ao estado real de maturidade (269 testes, PR-07 done)
- `done` sem claims exageradas — demo é honesto sobre estado do fluxo
- `done` exemplos usando o fluxo real introduzido nas PRs anteriores

### Critérios de aceite
- `done` nenhuma claim central contradiz o comportamento implementado
- `done` exemplos viram smoke tests úteis
- `done` números e status do backlog refletem o que está pronto

## PR-08 — Observabilidade e rastreabilidade operacional
**Status:** `done`

### Objetivo
Padronizar event log, métricas e decisões operacionais sem reabrir aprovação.

### Decisão de encaminhamento
- `docs/0021-sprint-04-observabilidade-e-event-log.md` encerrou este ciclo com itens 1 a 3 concluídos.
- Esta PR preserva o estado aprovado da entrega e consolidou a rastreabilidade mínima incremental.

## Backlog complementar
### Só depois de PR-01 a PR-06
- revisar P2 com base em dados reais: dashboard, scoring por agente, sprint history, patterns
- revisar P3 com base em contratos estáveis: multi-project, domain optimization, comparative intelligence, runtime automation avançado

## Definition of Done por PR
- `done` testes existentes passando
- `done` testes novos cobrindo o gap corrigido
- `done` documentação afetada atualizada
- `done` sem campos duplicados ou aliases silenciosos sem justificativa
- `done` artefatos gerados compatíveis com contratos e consumidores

## Sequência recomendada de merge
1. PR-01
2. PR-02
3. PR-03
4. PR-04
5. PR-05
6. PR-06
7. PR-07
8. PR-08

## Resultado esperado ao final
Ao fim de PR-08, o projeto deve sair do estado “framework contratual com vários stubs” para “núcleo operacional coerente, auditável e integrável”. PR-07 e PR-08 fecham o alinhamento entre o que o projeto promete e o que realmente entrega.

## Fechamento atual
- `done` PR-01, PR-02, PR-03, PR-04, PR-05, PR-06, PR-07, PR-08 — todos fechados
- Sprint 02 aplicada em 2026-04-16

- Auditoria de estado real registrada em `docs/0028-relatorio-de-auditoria-do-estado-real.md`.
- O ciclo operacional incremental mais recente está consolidado em `docs/0044-sprint-18-cli-canonico-de-operacao.md`.
- A auditoria mais recente do estado real está em `docs/0046-relatorio-de-auditoria-pos-sprint-18.md`.
- O ciclo incremental mais recente está consolidado em `docs/0064-sprint-36-politicas-configuraveis-por-projeto.md`.
## Atualização de aprovação
A auditoria de Sprint 02 resolveu todos os bloqueios e a entrega foi **aprovada**.

Estado documentado em:
- [0018-sprint-02-checklist-e-patch-plan.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0018-sprint-02-checklist-e-patch-plan.md:1)
- [0019-checklist-final-de-aprovacao.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0019-checklist-final-de-aprovacao.md:1)
- [0020-sprint-03-consolidacao-documental.md](/home/ricardo/.openclaw/workspace/cvg-harness/docs/0020-sprint-03-consolidacao-documental.md:1) — rodada final de consolidação documental e polimento
- Auditoria pós-Sprint 12 registrada em `docs/0034-relatorio-de-auditoria-pos-sprint-12.md`.
- Auditoria pós-Sprint 18 registrada em `docs/0046-relatorio-de-auditoria-pos-sprint-18.md`.
