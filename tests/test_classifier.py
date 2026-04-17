"""
Testes para o módulo de classificação.
"""

import pytest
from cvg_harness.classification.classifier import (
    classify, validate_classification, calculate_mode, ScoreLevel
)


def test_fast_mode_score_below_9():
    dims = {
        "impacto_arquitetural": 1,
        "modulos_afetados": 1,
        "risco_de_regressao": 1,
        "criticidade_de_negocio": 1,
        "sensibilidade_de_dados": 0,
        "dependencia_externa": 0,
        "reversibilidade": 1,
        "complexidade_de_validacao": 1,
    }
    result = classify("proj", "demo", dims, "low impact")
    assert result.mode == "FAST"
    assert result.total_score == 6


def test_enterprise_mode_score_above_9():
    dims = {
        "impacto_arquitetural": 2,
        "modulos_afetados": 2,
        "risco_de_regressao": 2,
        "criticidade_de_negocio": 2,
        "sensibilidade_de_dados": 1,
        "dependencia_externa": 1,
        "reversibilidade": 1,
        "complexidade_de_validacao": 1,
    }
    result = classify("proj", "demo", dims, "moderate impact")
    assert result.mode == "ENTERPRISE"
    assert result.total_score == 12


def test_enterprise_mode_critical_dimension():
    dims = {
        "impacto_arquitetural": 3,
        "modulos_afetados": 0,
        "risco_de_regressao": 0,
        "criticidade_de_negocio": 0,
        "sensibilidade_de_dados": 0,
        "dependencia_externa": 0,
        "reversibilidade": 0,
        "complexidade_de_validacao": 0,
    }
    result = classify("proj", "demo", dims, "structural change")
    assert result.mode == "ENTERPRISE"


def test_override_forces_enterprise():
    dims = {
        "impacto_arquitetural": 1,
        "modulos_afetados": 1,
        "risco_de_regressao": 1,
        "criticidade_de_negocio": 1,
        "sensibilidade_de_dados": 1,
        "dependencia_externa": 1,
        "reversibilidade": 1,
        "complexidade_de_validacao": 1,
    }
    result = classify("proj", "demo", dims, "override", override=True, override_reason="legal requirement")
    assert result.mode == "ENTERPRISE"
    assert result.override_applied is True
    assert result.override_reason == "legal requirement"


def test_validate_classification_valid():
    result = classify("proj", "demo", {"impacto_arquitetural": 1}, "test")
    errors = validate_classification(result)
    assert errors == []


def test_validate_classification_missing_rationale():
    result = classify("proj", "demo", {"impacto_arquitetural": 1}, "")
    errors = validate_classification(result)
    assert "rationale vazio" in errors
