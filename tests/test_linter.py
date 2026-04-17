"""
Testes para o Spec Linter.
"""

import pytest
from cvg_harness.linter.spec_linter import lint_spec, SpecLinter


def test_lint_spec_passes_with_valid_spec():
    spec = {
        "version": "v1",
        "criterios": [
            {"descricao": "API retorna 200", "testavel": True},
        ],
        "modulos": ["auth", "api"],
        "edge_cases": ["token expirado", "payload vazio"],
        "limite_escopo": "apenas auth",
        "areas_proibidas": ["legacy"],
        "contratos": [],
        "fluxo_critico": False,
        "rollback": "reverter migração",
        "observabilidade": "logs básicos",
    }
    linter = SpecLinter(mode="FAST")
    report = linter.lint(spec)
    assert report.result == "PASS"
    assert report.blocking_issues == 0


def test_lint_spec_fails_vague_module():
    spec = {
        "version": "v1",
        "criterios": [{"descricao": "teste", "testavel": True}],
        "modulos": ["x"],
        "edge_cases": [],
        "limite_escopo": "algo",
        "contratos": [],
    }
    linter = SpecLinter(mode="FAST")
    report = linter.lint(spec)
    assert report.result == "FAIL"
    assert report.blocking_issues > 0
    assert any(f["rule"] == "vague_module" for f in report.findings)


def test_lint_spec_missing_edge_cases_enterprise():
    spec = {
        "version": "v1",
        "criterios": [{"descricao": "teste", "testavel": True}],
        "modulos": ["auth"],
        "edge_cases": [],
        "limite_escopo": "auth",
        "contratos": [],
    }
    linter = SpecLinter(mode="ENTERPRISE")
    report = linter.lint(spec)
    assert report.blocking_issues > 0
    assert any(f["rule"] == "missing_edge_cases" for f in report.findings)


def test_lint_spec_missing_scope_limit():
    spec = {
        "version": "v1",
        "criterios": [{"descricao": "teste", "testavel": True}],
        "modulos": ["auth"],
        "edge_cases": [],
        "contratos": [],
    }
    linter = SpecLinter(mode="FAST")
    report = linter.lint(spec)
    assert report.result == "FAIL"
    assert any(f["rule"] == "missing_scope_limit" for f in report.findings)


def test_lint_spec_unittestable_criterion():
    spec = {
        "version": "v1",
        "criterios": [
            {"descricao": "deve funcionar bem", "testavel": False},
        ],
        "modulos": ["auth"],
        "edge_cases": [],
        "limite_escopo": "auth",
        "contratos": [],
    }
    linter = SpecLinter(mode="FAST")
    report = linter.lint(spec)
    assert report.result == "FAIL"
    assert any(f["rule"] == "unittestable_criterion" for f in report.findings)


def test_lint_spec_lacuna_criterion_is_allowed():
    """Lacunas explícitas não bloqueiam o SPEC imediatamente."""
    spec = {
        "version": "v1",
        "criterios": [
            {
                "descricao": "Feature implementada e funcionando",
                "testavel": False,
                "definido_como_lacuna": True,
            },
        ],
        "modulos": ["auth"],
        "edge_cases": ["token inválido"],
        "limite_escopo": "autenticação",
        "contratos": [],
        "areas_proibidas": [],
    }
    linter = SpecLinter(mode="FAST")
    report = linter.lint(spec)
    assert report.result == "PASS"
    assert report.blocking_issues == 0


def test_lint_spec_accepts_contextual_contract_metadata():
    """Metadata rica de contratos não quebra o lint quando a SPEC continua válida."""
    spec = {
        "version": "v1",
        "criterios": [
            {"descricao": "API retorna 200", "testavel": True},
        ],
        "modulos": ["auth", "api", "release"],
        "edge_cases": ["token expirado", "payload vazio"],
        "limite_escopo": "apenas auth",
        "areas_proibidas": ["legacy"],
        "contratos": [
            {
                "nome": "auth_session",
                "tipo": "auth",
                "criticidade": "high",
                "superficie": "auth",
                "evidencia_minima": ["login bem-sucedido"],
            }
        ],
        "fluxo_critico": False,
        "rollback": "reverter auth e limpar sessões ativas",
        "observabilidade": "logs estruturados de auth, correlação de sessão e métricas de login/logout",
    }
    linter = SpecLinter(mode="FAST")
    report = linter.lint(spec)
    assert report.result == "PASS"
    assert report.blocking_issues == 0


def test_lint_score_calculation():
    spec = {
        "version": "v1",
        "criterios": [{"descricao": "teste", "testavel": False}],
        "modulos": ["x"],
        "edge_cases": [],
        "contratos": [],
    }
    linter = SpecLinter(mode="FAST")
    report = linter.lint(spec)
    assert report.score <= 100
    assert report.score >= 0
