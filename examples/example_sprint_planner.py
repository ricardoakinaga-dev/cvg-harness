#!/usr/bin/env python3
"""
Exemplo: Sprint Planner
Quebra SPEC em sprints executáveis.
"""

from cvg_harness.sprint.sprint_planner import SprintPlanner, save_sprint_plan

# SPEC para modo FAST - sprint única
spec_fast = {
    "version": "v1",
    "meta": "adição de campo de status",
    "modulos": ["auth"],
    "criterios": [
        {"descricao": "campo status adicionado", "testavel": True},
        {"descricao": "API retorna campo", "testavel": True},
    ],
    "edge_cases": ["null value", "empty string"],
}

planner = SprintPlanner()
plan_fast = planner.plan(spec_fast, mode="FAST")
print(f"Modo FAST: {len(plan_fast.sprints)} sprint(s)")
for sprint in plan_fast.sprints:
    print(f"  {sprint.sprint_id}: {sprint.escopo}")
    print(f"  Agente: {sprint.agente}")
    print(f"  Risco: {sprint.risco}")
print()

# SPEC para modo ENTERPRISE - múltiplas sprints
spec_ent = {
    "version": "v1",
    "meta": "novo sistema de autenticação OAuth2",
    "modulos": ["auth/oauth2", "api/v2", "middleware/jwt"],
    "criterios": [
        {"descricao": "OAuth2 login funciona", "testavel": True},
        {"descricao": "JWT validation funciona", "testavel": True},
    ],
    "edge_cases": ["token expirado", "oauth provider down"],
}

plan_ent = planner.plan(spec_ent, mode="ENTERPRISE")
print(f"Modo ENTERPRISE: {len(plan_ent.sprints)} sprint(s)")
for sprint in plan_ent.sprints:
    print(f"  {sprint.sprint_id}: {sprint.escopo}")
    print(f"  Módulos: {sprint.modulos}")
    print(f"  Dependências: {sprint.dependencies}")
    print(f"  Bloqueado por: {sprint.blocked_by}")
    print(f"  Risco: {sprint.risco}")
print()

# Validação de sprint
errors = planner.validate_sprint(plan_ent.sprints[0], spec_ent)
print(f"Validação SPRINT-1: {'OK' if not errors else errors}")
