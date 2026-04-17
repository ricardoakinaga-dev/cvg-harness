#!/usr/bin/env python3
"""
Exemplo: Research → PRD → Spec Builder
Fluxo de criação de especificação.
"""

from cvg_harness.research.research_agent import ResearchAgent
from cvg_harness.prd.prd_agent import PRDAgent
from cvg_harness.spec_builder.spec_builder import SpecBuilderAgent

# 1. Research Agent
print("=== RESEARCH AGENT ===")
research_agent = ResearchAgent()
classification = {"mode": "ENTERPRISE", "total_score": 15}
research, system_map = research_agent.investigate("projeto-x", "OAuth2 authentication", classification)

print(f"Research - Módulos impactados: {research.modulos_impactados}")
print(f"Research - Riscos: {research.riscos}")
print(f"Research - Dependências: {research.dependencias_conhecidas}")
print(f"\nSystem Map - Módulos: {system_map.modulos}")
print(f"System Map - Zonas críticas: {system_map.zonas_criticas}")
print(f"System Map - Boundaries: {system_map.boundaries}")
print()

# 2. PRD Agent
print("=== PRD AGENT ===")
prd_agent = PRDAgent()
prd = prd_agent.create_prd(
    project="projeto-x",
    feature="OAuth2 authentication",
    research_notes=research.to_dict(),
    classification=classification,
)

print(f"PRD - Problema: {prd.problema}")
print(f"PRD - Objetivo: {prd.objetivo}")
print(f"PRD - Escopo: {prd.escopo}")
print(f"PRD - Fora de escopo: {prd.fora_de_escopo}")
print(f"PRD - KPIs: {prd.kpis}")
print(f"PRD - User Stories: {prd.user_stories}")
print(f"PRD - Riscos: {prd.riscos}")
print()

# 3. Spec Builder Agent
print("=== SPEC BUILDER AGENT ===")
spec_builder = SpecBuilderAgent()
spec = spec_builder.build(
    prd=prd.to_dict(),
    research_notes=research.to_dict(),
    classification=classification,
)

print(f"SPEC - Meta: {spec.meta}")
print(f"SPEC - Módulos: {spec.modulos}")
print(f"SPEC - Áreas autorizadas: {spec.areas_autorizadas}")
print(f"SPEC - Áreas proibidas: {spec.areas_proibidas}")
print(f"SPEC - Critérios: {len(spec.criterios)} critérios")
print(f"SPEC - Edge cases: {spec.edge_cases}")
print(f"SPEC - Fluxo crítico: {spec.fluxo_critico}")
print(f"SPEC - Observabilidade: {spec.observabilidade}")
print(f"SPEC - Rollback: {spec.rollback}")
