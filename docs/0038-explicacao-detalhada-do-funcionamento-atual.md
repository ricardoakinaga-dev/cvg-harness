# 0038. Explicação detalhada do funcionamento atual do CVG Harness

## Objetivo
Registrar, de forma fiel ao estado atual do repositório, como o `cvg-harness` funciona hoje, quais etapas ele executa, quais artefatos produz e quais problemas ele resolve na prática.

## Visão geral
O `cvg-harness` é um framework operacional para transformar uma demanda de software em um fluxo controlado, auditável e progressivo.

Ele não funciona como um gerador de código direto. O desenho atual força a passagem por uma cadeia de decisões e validações:

`Classificação -> Research -> PRD -> SPEC -> Sprint Plan -> Validação -> Release Readiness -> Métricas`

Essa sequência reduz improviso, explicita escopo e registra evidência do que aconteceu em cada fase.

## Como o programa funciona hoje

### 1. Classificação da demanda
O primeiro passo é classificar a mudança como `FAST` ou `ENTERPRISE`.

O classificador usa dimensões de risco e impacto, como:
- impacto arquitetural
- módulos afetados
- risco de regressão
- criticidade de negócio
- sensibilidade de dados
- dependência externa
- reversibilidade
- complexidade de validação

Se o score é alto ou há dimensão crítica, o fluxo tende para `ENTERPRISE`.

Artefato gerado:
- `classification.json`

Função central:
- [`src/cvg_harness/classification/classifier.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/classification/classifier.py)

### 2. Research
O `ResearchAgent` examina o workspace e tenta usar sinais reais do repositório antes de cair em heurística.

Ele separa:
- fatos observados
- hipóteses
- riscos
- restrições
- dúvidas
- módulos impactados
- dependências conhecidas

Também gera um `system-map` com módulos, arquivos da área, boundaries e zonas críticas.

Artefatos gerados:
- `research-notes.json`
- `research-notes.md`
- `system-map.json`
- `system-map.md`

Função central:
- [`src/cvg_harness/research/research_agent.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/research/research_agent.py)

### 3. PRD
O `PRDAgent` transforma o research em um documento de produto.

Ele define:
- problema
- objetivo
- escopo
- fora de escopo
- KPIs
- user stories
- riscos
- critérios de aceite

O PRD não nasce genérico. Ele é derivado do contexto observado no research.

Artefatos gerados:
- `prd.json`
- `prd.md`

Função central:
- [`src/cvg_harness/prd/prd_agent.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/prd/prd_agent.py)

### 4. SPEC
O `SpecBuilderAgent` converte PRD + research em uma especificação técnica executável.

Ele define:
- módulos afetados
- áreas autorizadas
- áreas proibidas
- contratos
- sprint planning de alto nível
- critérios de aceite
- edge cases
- observabilidade
- rollback
- limite de escopo
- se a mudança é estrutural

Os contratos agora carregam metadata de risco, como criticidade, superfície e evidência mínima.

Artefatos gerados:
- `spec.json`
- `spec.md`

Função central:
- [`src/cvg_harness/spec_builder/spec_builder.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/spec_builder/spec_builder.py)

### 5. Sprint planning
O planejador quebra a SPEC em sprints executáveis.

O orquestrador persiste:
- `sprint-plan.json`
- `execution-order.json`

Isso garante que a ordem de execução não fique só embutida de forma implícita em outro artefato.

Função central:
- [`src/cvg_harness/flow.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/flow.py)

### 6. Validações
O fluxo inclui quatro controles centrais:

- `Spec Linter`
  - bloqueia SPEC ambígua, incompleta ou não testável.
- `Architecture Guardian`
  - bloqueia mudança fora da área autorizada.
- `Evaluator`
  - valida a sprint contra evidência concreta.
- `Drift Detector`
  - compara intenção, plano, execução e release readiness.

Funções centrais:
- [`src/cvg_harness/linter/spec_linter.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/linter/spec_linter.py)
- [`src/cvg_harness/guardian/architecture_guardian.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/guardian/architecture_guardian.py)
- [`src/cvg_harness/evaluator/evaluator.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/evaluator/evaluator.py)
- [`src/cvg_harness/drift/drift_detector.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/drift/drift_detector.py)

### 7. Release readiness
O `ReleaseReadinessEngine` consolida os gates `GATE_0` a `GATE_9`.

O resultado pode ser:
- `APPROVED`
- `REJECTED`
- `CONDITIONAL`

Se algo relevante estiver faltando, a release não é liberada.

Função central:
- [`src/cvg_harness/release/release_readiness.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/release/release_readiness.py)

### 8. Estado, eventos e métricas
O programa registra tudo que importa em artefatos persistentes:

- `flow-state.json`
- `progress.json`
- `event-log.jsonl`
- `reports/gates/*.json`
- `reports/*.json`

Além disso, o `MetricsAggregator` calcula métricas operacionais a partir de eventos reais e progresso real.

Artefato canônico:
- `delivery-metrics.json`

Funções centrais:
- [`src/cvg_harness/ledger/progress_ledger.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/ledger/progress_ledger.py)
- [`src/cvg_harness/ledger/event_log.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/ledger/event_log.py)
- [`src/cvg_harness/metrics_agg/metrics_aggregator.py`](/home/ricardo/.openclaw/workspace/cvg-harness/src/cvg_harness/metrics_agg/metrics_aggregator.py)

## Exemplos de uso

### Uso rápido da CLI
```bash
cvg classify --project x --demand "novo login" --dimensions '{"impacto_arquitetural":3,"modulos_afetados":2,"risco_de_regressao":3}' --rationale "mudança crítica"
cvg lint --spec spec.json --mode ENTERPRISE
cvg guard --files "src/auth/login.py" --authorized '["src/auth"]' --prohibited '["src/legacy"]'
cvg drift --intake intake.json --prd prd.json --spec spec.json
cvg progress new --project x --feature y --mode FAST
cvg event --log event-log.jsonl --add "sprint_approved|Evaluator|evaluation-report.json"
cvg handoff --source prd.md --target "Spec Builder" --objective "gerar spec"
```

### Uso do fluxo completo em Python
```python
from pathlib import Path
from cvg_harness.flow import FlowOrchestrator

orch = FlowOrchestrator(
    project="meu-projeto",
    feature="adicionar autenticação OAuth2",
    mode="ENTERPRISE",
    workspace=Path("./.cvg-harness"),
)

orch.classify(
    dimensions={
        "impacto_arquitetural": 3,
        "modulos_afetados": 2,
        "risco_de_regressao": 3,
        "criticidade_de_negocio": 3,
        "sensibilidade_de_dados": 3,
        "dependencia_externa": 2,
        "reversibilidade": 1,
        "complexidade_de_validacao": 2,
    },
    rationale="mudança crítica de segurança",
)
orch.run_research()
orch.run_prd()
orch.build_spec()
orch.run_lint()
orch.plan_sprints()
orch.check_guard(["src/auth/login.py"])
orch.evaluate_sprint(["testes", "logs", "arquivos alterados"], round_num=1)
orch.detect_drift()
orch.check_release_readiness()
```

### Uso do demo completo
```bash
python3 examples/demo_complete_flow.py
```

Esse demo executa o fluxo inteiro e mostra:
- classificação
- research
- PRD
- SPEC
- lint
- sprint plan
- guard
- drift
- evaluation
- release readiness
- métricas

## Que problemas o programa resolve

### 1. Demanda vaga demais
Transforma uma ideia em artefatos formais.

### 2. Código antes do planejamento
Força a sequência correta: entender, documentar, especificar, validar, depois executar.

### 3. Escopo mudando no meio do caminho
Explicita o que entra e o que fica fora.

### 4. Risco arquitetural invisível
Bloqueia alterações fora da área autorizada.

### 5. Release decidida no improviso
Consolida gates e evidências antes da promoção.

### 6. Métricas inventadas
Calcula métricas a partir de eventos e progresso reais.

## Limites atuais

- o runtime externo existe, mas é seguro por padrão e não é uma automação irrestrita;
- a integração com execução real de hooks é opt-in;
- as frentes de observabilidade mais profundas e guardrails avançados ainda são áreas de evolução incremental;
- o sistema é um harness operacional, não um substituto automático de produto ou engenharia.

## Conclusão
O `cvg-harness` hoje funciona como um sistema de governança para trabalho de software.
Ele organiza a demanda, reduz ambiguidade, protege a arquitetura, rastreia execução e cria uma trilha clara até a release.

