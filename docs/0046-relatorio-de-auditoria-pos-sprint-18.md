# 0046 - Relatório de auditoria pós-Sprint 18

## Objetivo

Comparar o que a documentação mais recente descreve com o que o repositório realmente entrega após a Sprint 18, usando evidência local do código, testes e demo.

## Base usada nesta auditoria

Documentação operacional considerada como fonte principal de verdade:
- `README.md`
- `docs/0039-operacao-real-do-cvg-harness.md`
- `docs/0040-design-do-cli-e-contratos-de-comando.md`
- `docs/0041-separacao-entre-engine-e-experiencia-operacional.md`
- `docs/0042-workspace-operacional-e-ciclo-de-vida-da-demanda.md`
- `docs/0043-limites-atuais-e-roadmap-de-terminal-orchestrator.md`
- `docs/0044-sprint-18-cli-canonico-de-operacao.md`
- `docs/0045-contratos-para-executores-externos.md`

Validação executada:
- `pytest -q` → `217/217` passando
- `python3 examples/demo_complete_flow.py` → `Fluxo: completed`, `Release: APPROVED`
- `python3 -m cvg_harness --help` e `python3 -m cvg_harness continue --help`

## Leitura geral

O projeto deixou de parecer apenas um framework modular e já funciona, de fato, como um CLI canônico de operação no terminal. O ganho principal da Sprint 18 foi de produto: agora existe entrada principal, loop operacional legível, persistência própria de run, retomada, aprovação humana explícita e uma separação clara entre modo operador e modo avançado.

Ainda assim, nem tudo está no teto de maturidade. Os principais limites residuais estão em:
- planning ainda parcialmente heurístico
- métricas ainda com partes estimadas, não sempre observadas
- integração com executor externo formalizada em contrato, mas ainda pouco acoplada ao fluxo canônico do operador
- evidência estruturada já entra no sistema, mas ainda é achatada para consumo do evaluator

## Achados principais

### 1. O modo operador agora é real, não só documental
A CLI já expõe e sustenta `run`, `status`, `inspect`, `continue`, `pause`, `approve`, `replan`, `events` e `metrics`, com help operador-first e primitives antigas preservadas.

### 2. O loop operacional existe no código
A run canônica já persiste estado em `.cvg-harness/`, cria `run.json`, `flow-state.json`, `progress.json`, `event-log.jsonl`, artefatos e relatórios, e consegue avançar até `release readiness` com decisão final.

### 3. `inspect` melhorou de verdade
Agora existe leitura causal de sprint, blockers, changed files, evidências, decisões e timeline relevante. Isso reduziu o gap entre "estado bruto" e "inspeção útil".

### 4. Evidência estruturada existe, mas ainda não é explorada profundamente
O operador já pode fornecer `--evidence`, `--evidence-json` e `--evidence-file`, e isso vira `execution-input.json` e `evidence-manifest.json`. Mas o evaluator ainda consome a versão achatada em texto.

### 5. Adaptadores externos foram formalizados sem quebrar a arquitetura
`ExternalExecutorAdapter`, `ExecutionDispatchRequest`, `ExecutionDispatchResult`, `ExternalExecutorRegistry` e `ExternalExecutorBridge` existem e preservam a separação entre orquestrador e executor. Ainda não são a experiência principal do operador.

## Notas por item

### 1. CLI canônico de operação — `93/100`
Muito forte. O modo operador está materializado no código, no help e no README. Perde poucos pontos porque ainda não existe comando explícito de dispatch para executor externo ou listagem de adapters na UX principal.

### 2. Loop operacional e retomada — `91/100`
`run -> approve -> continue -> evaluate -> drift -> release` funciona e persiste estado. Ainda pode melhorar na clareza de rounds/retries e em transições com executor externo real.

### 3. Workspace operacional e persistência — `94/100`
A estrutura `.cvg-harness/` já sustenta retomada, inspeção e auditoria. Boa clareza e boa separação por run.

### 4. Research Engine — `76/100`
Saiu do estado cego e já usa evidência local do codebase quando existe. Ainda depende de heurística em vários cenários e não faz leitura semântica profunda do repositório.

### 5. PRD Engine — `80/100`
Hoje o PRD já deriva problema, objetivo, escopo e critérios a partir do research real. Continua mais forte em estruturação do que em descoberta profunda.

### 6. Spec Builder — `88/100`
A SPEC já é bem mais operacional, com contratos, criticidade, superfície, evidência mínima, observabilidade e rollback. Ainda pode evoluir na profundidade contextual por domínio.

### 7. Spec Linter — `92/100`
Bloco maduro, consistente com a governança e bem coberto por testes.

### 8. Sprint Planner — `85/100`
Já gera sprint plan e `execution-order.json`, e alimenta o fluxo real. Ainda não expressa dependências/paralelismo em profundidade alta.

### 9. Flow Orchestrator — `90/100`
Hoje sustenta planning, gates, release e fechamento do ciclo. Continua sendo a espinha dorsal correta do produto.

### 10. Gates e política de aprovação — `91/100`
Gates formais persistidos, eventos causais e política consistente no fluxo atual. Já está em bom nível de maturidade.

### 11. Architecture Guardian — `86/100`
Boundary, áreas proibidas, escopo e casos de waiver estão sólidos. Ainda não é um analisador arquitetural profundo; continua intencionalmente focado nas regras mais governáveis.

### 12. Evaluator / ingestão de evidência — `82/100`
Evaluator está estável e a ingestão de evidência melhorou bastante com JSON/arquivo. O ponto que segura a nota é que a avaliação ainda trabalha sobre evidência achatada e não explora todo o schema estruturado.

### 13. Drift Detector — `86/100`
Explica melhor findings, cobre mais camadas e já conversa com evaluation/release. Ainda pode melhorar em correlação causal com rounds e artefatos externos.

### 14. Release Readiness — `90/100`
Readiness canônico em `release-readiness-report.json`, gates consolidados e decisão final coerente. Está forte.

### 15. Progress Ledger + Event Log — `89/100`
Já são trilha real e útil. Ganharam bastante com eventos de gate e de operador. Ainda há espaço para mais semântica causal por round e por sprint.

### 16. Metrics Aggregator — `80/100`
Melhorou e já produz leitura útil no fluxo feliz. Ainda mistura valores reais com estimativas controladas, principalmente custo e lead time em cenários de demo.

### 17. Runtime seguro e hooks — `86/100`
A base está boa, com modo simulado, execução real opt-in e testes dedicados. Continua separado do fluxo operador principal, o que é correto, mas reduz a sensação de integração ponta a ponta.

### 18. Adaptadores para executores externos — `74/100`
O contrato já existe e está certo arquiteturalmente. A nota ainda é moderada porque isso ainda é preparação de integração, não operação canônica consumida pela CLI do dia a dia.

### 19. README + documentação operacional recente — `91/100`
A documentação mais nova (`0039` a `0045` + README) já está bem alinhada ao código. Há fidelidade maior do que em fases anteriores.

### 20. Aderência documental geral do repositório — `84/100`
A trilha principal está boa, mas o diretório `docs/` ainda carrega muitas camadas históricas de sprints antigas, auditorias e numeração duplicada. Isso não quebra o produto, mas reduz legibilidade global.

## Nota global

**87/100**

## O que melhorou desde o estado anterior

- entrada canônica de produto no terminal
- separação explícita entre modo operador e modo avançado
- `inspect` com causalidade real
- evidência estruturada além de texto livre
- contratos formais para executores externos
- documentação recente muito mais alinhada ao código real

## O que ainda segura a nota

- planning ainda parcialmente heurístico
- evaluator ainda não usa toda a riqueza da evidência estruturada
- adaptadores externos ainda não viraram superfície operacional principal
- métricas continuam parcialmente estimadas
- diretório `docs/` ainda é historicamente pesado

## Atualização de estado

- A evidência estruturada passou a chegar ao `Evaluator` sem flatten obrigatório no caminho do operador.
- O relatório de avaliação agora preserva um resumo estruturado das evidências reconhecidas, além do texto legível já existente.

## Recomendação objetiva para o próximo sprint

Abrir um sprint curto focado em **integração controlada com executor externo e evidência operacional estruturada**, sem reescrever a UX principal.

Frentes recomendadas:
1. permitir `inspect` mostrar dispatch plan de executor externo quando existir
2. plugar `ExternalExecutorBridge` ao modo operador como hand-off explícito, não automático
3. fazer o evaluator consumir parte do schema estruturado de evidência sem depender só do flatten textual
4. enriquecer métricas com sinal vindo de dispatch/execução externa real quando disponível
