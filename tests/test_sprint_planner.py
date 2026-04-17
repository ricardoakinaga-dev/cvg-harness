"""
Testes para Sprint Planner.
"""

import pytest
import tempfile
import json
from pathlib import Path

from cvg_harness.sprint.sprint_planner import SprintPlanner, Sprint, SprintPlan, save_sprint_plan, load_sprint_plan


def test_sprint_planner_fast_mode():
    """Em modo FAST, gera sprint única."""
    planner = SprintPlanner()
    spec = {
        "version": "v1",
        "meta": "adição de campo",
        "modulos": ["auth"],
        "criterios": [{"descricao": "campo adicionado"}],
        "edge_cases": [],
    }
    plan = planner.plan(spec, mode="FAST")
    assert len(plan.sprints) == 1
    assert plan.execution_order == ["SPRINT-1"]
    assert plan.mode == "FAST"


def test_sprint_planner_enterprise_mode():
    """Em modo ENTERPRISE, quebra por módulo."""
    planner = SprintPlanner()
    spec = {
        "version": "v1",
        "meta": "sistema de auth",
        "modulos": ["auth", "api", "middleware"],
        "criterios": [{"descricao": "teste"}],
        "edge_cases": [],
    }
    plan = planner.plan(spec, mode="ENTERPRISE")
    assert len(plan.sprints) == 3
    assert plan.execution_order == ["SPRINT-1", "SPRINT-2", "SPRINT-3"]
    assert plan.mode == "ENTERPRISE"


def test_sprint_dependencies():
    """Sprints em ENTERPRISE têm dependências."""
    planner = SprintPlanner()
    spec = {
        "version": "v1",
        "meta": "test",
        "modulos": ["a", "b"],
        "criterios": [],
        "edge_cases": [],
    }
    plan = planner.plan(spec, mode="ENTERPRISE")
    assert plan.sprints[0].blocked_by == []
    assert plan.sprints[1].blocked_by == ["SPRINT-1"]


def test_validate_sprint():
    """Validação de sprint bem formada."""
    planner = SprintPlanner()
    sprint = Sprint(
        sprint_id="SPRINT-1",
        escopo="teste",
        agente="coder",
        modulos=["auth"],
        criterios=["teste"],
        evidencias=["log"],
    )
    errors = planner.validate_sprint(sprint, {})
    assert errors == []


def test_validate_sprint_missing_fields():
    """Validação detecta campos faltantes."""
    planner = SprintPlanner()
    sprint = Sprint(sprint_id="", escopo="", agente="", modulos=[])
    errors = planner.validate_sprint(sprint, {})
    assert len(errors) >= 3


def test_sprint_plan_persistence():
    """Salva e carrega sprint plan."""
    planner = SprintPlanner()
    spec = {"version": "v1", "meta": "test", "modulos": ["a"], "criterios": [], "edge_cases": []}
    plan = planner.plan(spec, mode="FAST")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        path = Path(f.name)

    save_sprint_plan(plan, path)
    loaded = load_sprint_plan(path)
    assert loaded.spec_version == "v1"
    assert len(loaded.sprints) == 1
    assert loaded.execution_order == ["SPRINT-1"]
    path.unlink()
