"""
P1-5: Templates revisados
Templates para PRD, SPEC e Sprint Plan.
"""

from __future__ import annotations

PRD_TEMPLATE = """# PRD: {titulo}

## Problema
{descricao_do_problema}

## Objetivo
{objetivo_mensuravel}

## KPIs
- {kpi_1}
- {kpi_2}

## Escopo
### Dentro do escopo
- {dentro_escopo_1}
- {dentro_escopo_2}

### Fora do escopo
- {fora_escopo_1}
- {fora_escopo_2}

## User Stories
1. Como [ator], quero [ação] para [resultado]
2. Como [ator], quero [ação] para [resultado]

## Riscos
- {risco_1}
- {risco_2}

## Critérios de Aceite
1. [Critério 1]
2. [Critério 2]
"""

SPEC_TEMPLATE = """# SPEC: {titulo}

## Meta
{meta_do_projeto}

## Módulos Afetados
- {modulo_1}
- {modulo_2}

## Áreas Autorizadas
- {area_autorizada_1}
- {area_autorizada_2}

## Áreas proibidas
- {area_proibida_1}
- {area_proibida_2}

## Regras de Negócio
1. {regra_1}
2. {regra_2}

## Fluxos
### Fluxo Principal
1. {passo_1}
2. {passo_2}

### Fluxo Alternativo
1. {passo_alt_1}

## Contratos
### {contrato_nome}
- Tipo: {tipo}
- Endpoint: {endpoint}
- Payload: {payload}

## Edge Cases
- {edge_case_1}
- {edge_case_2}

## Critérios de Aceite
| Critério | Testável | Lacuna |
|----------|----------|--------|
| {criterio_1} | sim | não |

## Rollback
{procedimento_rollback}

## Observabilidade
- Logs: {logs}
- Métricas: {metricas}
"""

SPRINT_PLAN_TEMPLATE = """# Sprint Plan: {sprint_id}

## Sprint {sprint_id}
- **Escopo**: {escopo}
- **Agente**: {agente}
- **Dependências**: {dependencias}
- **Evidências esperadas**: {evidencias}

## Critérios de Aceite
1. {criterio_1}
2. {criterio_2}

## Arquivos esperados
- {arquivo_1}
- {arquivo_2}

## Risco
{risco}
"""

EXECUTION_ORDER_TEMPLATE = """# Execution Order

## Sequência de Sprints
{sequencia}

## Bloqueios
{bloqueios}

## Paralelismo Permitido
{paralelismo}

## Pré-condições
{pre_conds}
"""


def render_prd(data: dict) -> str:
    return PRD_TEMPLATE.format(**data)


def render_spec(data: dict) -> str:
    return SPEC_TEMPLATE.format(**data)


def render_sprint_plan(data: dict) -> str:
    return SPRINT_PLAN_TEMPLATE.format(**data)


def render_execution_order(data: dict) -> str:
    return EXECUTION_ORDER_TEMPLATE.format(**data)
