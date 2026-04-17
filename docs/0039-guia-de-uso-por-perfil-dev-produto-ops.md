# 0039. Guia de uso por perfil: dev, produto e ops

## Objetivo
Mostrar como cada perfil usa o `cvg-harness` no dia a dia e quais comandos ou artefatos importam mais para cada contexto.

## 1. Perfil dev

### O que o dev faz com o harness
- entende o escopo antes de codar
- valida se a SPEC é executável
- evita tocar áreas proibidas
- registra evidências do que foi feito
- confere se a release foi bloqueada por algo objetivo

### Fluxo típico
```bash
cvg classify --project x --demand "feature" --dimensions '{"impacto_arquitetural":2,"modulos_afetados":2,"risco_de_regressao":2}' --rationale "mudança moderada"
cvg lint --spec spec.json --mode FAST
cvg guard --files "src/module/file.py" --authorized '["src/module"]' --prohibited '["src/legacy"]'
cvg drift --intake intake.json --prd prd.json --spec spec.json
```

### O que o dev ganha
- menos retrabalho
- SPEC mais clara
- bloqueio precoce de mudanças fora de escopo
- trilha de evidência para revisão e release

## 2. Perfil produto

### O que produto faz com o harness
- transforma a demanda em problema, objetivo e escopo
- controla fora de escopo
- acompanha critérios de aceite
- entende riscos antes de liberar implementação

### Fluxo típico
```bash
cvg classify --project x --demand "melhorar onboarding" --dimensions '{"criticidade_de_negocio":3,"risco_de_regressao":2,"sensibilidade_de_dados":1}' --rationale "fluxo importante para conversão"
python3 examples/example_research_prd_spec.py
```

### O que produto ganha
- PRD menos genérico
- critérios de sucesso mais claros
- escopo e fora de escopo explícitos
- alinhamento melhor entre problema e solução

## 3. Perfil ops

### O que ops faz com o harness
- acompanha fluxo, gates e bloqueios
- inspeciona event log
- revisa progress ledger
- consulta release readiness
- lê métricas operacionais

### Fluxo típico
```bash
cvg progress new --project x --feature y --mode ENTERPRISE
cvg event --log event-log.jsonl --query release_approved
cvg-repl
python3 examples/demo_complete_flow.py
```

### O que ops ganha
- rastreabilidade de aprovação
- visibilidade de bloqueios
- métricas reais do fluxo
- leitura operacional do estado atual

## Como cada perfil enxerga o sistema

### Dev
Vê o harness como guardrail técnico para evitar código sem contexto e mudanças fora de área autorizada.

### Produto
Vê o harness como máquina de redução de ambiguidade e de formalização de escopo.

### Ops
Vê o harness como fonte de estado, eventos, métricas e decisão final sobre release.

## Resumo prático

- se você escreve código, comece por `classify`, `research`, `prd` e `spec`;
- se você define produto, concentre-se em PRD, escopo, riscos e critérios;
- se você opera o fluxo, acompanhe `progress.json`, `event-log.jsonl`, `release-readiness-report.json` e `delivery-metrics.json`.

