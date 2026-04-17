"""
PR-01: Testes de unificação de schemas e contratos
Valida que classification.json produzido pelo classificador
passa na validação contratual e é aceito pelo evaluate_gate.
"""

import pytest
import tempfile
from pathlib import Path

from cvg_harness.classification.classifier import classify, save_classification, load_classification
from cvg_harness.contracts.artifact_contracts import validate_artifact, get_contract
from cvg_harness.gates.gate_policy import evaluate_gate


class TestClassificationSchemaContract:
    """Valida que classification.json do classificador é compatível com o contrato."""

    def test_classification_result_matches_contract_required_fields(self):
        """Os campos produzidos por classify()satisfazem o contrato de classification.json."""
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
        result = classify("proj", "demanda", dims, "mudança local")
        data = result.to_dict()

        # O contrato de classification.json deve validar sem erros
        errors = validate_artifact("classification.json", data)
        assert errors == [], f"Contract validation failed: {errors}"

    def test_classification_persists_and_loads_correctly(self):
        """ClassificationResult persistido e carregado mantém compatibilidade."""
        dims = {
            "impacto_arquitetural": 2,
            "modulos_afetados": 1,
            "risco_de_regressao": 1,
            "criticidade_de_negocio": 1,
            "sensibilidade_de_dados": 1,
            "dependencia_externa": 1,
            "reversibilidade": 1,
            "complexidade_de_validacao": 1,
        }
        result = classify("proj-x", "auth oauth2", dims, "critical change", override=True, override_reason="security")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "classification.json"
            save_classification(result, path)
            loaded = load_classification(path)

        # Carregado mantém todos os campos obrigatórios
        loaded_data = loaded.to_dict()
        errors = validate_artifact("classification.json", loaded_data)
        assert errors == [], f"Loaded classification failed contract: {errors}"

    def test_classification_enterprise_mode_passes_contract(self):
        """Classificação ENTERPRISE também satisfaz o contrato."""
        dims = {
            "impacto_arquitetural": 3,
            "modulos_afetados": 2,
            "risco_de_regressao": 3,
            "criticidade_de_negocio": 3,
            "sensibilidade_de_dados": 3,
            "dependencia_externa": 2,
            "reversibilidade": 1,
            "complexidade_de_validacao": 2,
        }
        result = classify("proj-y", "sistema critico", dims, "alta complexidade")
        data = result.to_dict()

        errors = validate_artifact("classification.json", data)
        assert errors == []
        assert result.mode == "ENTERPRISE"


class TestGateEvaluationWithRealClassification:
    """Valida que evaluate_gate(GATE_0) funciona com classification.json real."""

    def test_gate_0_accepts_valid_classification(self):
        """GATE_0 aprova classification.json válido."""
        dims = {
            "impacto_arquitetural": 1,
            "modulos_afetados": 1,
            "risco_de_regressao": 1,
            "criticidade_de_negocio": 0,
            "sensibilidade_de_dados": 0,
            "dependencia_externa": 0,
            "reversibilidade": 1,
            "complexidade_de_validacao": 1,
        }
        result = classify("proj", "feature", dims, "low impact")
        artifact_data = result.to_dict()

        gate_result = evaluate_gate("GATE_0", artifact_data)
        assert gate_result.state == "approved", f"GATE_0 should approve: {gate_result.blockers}"
        assert gate_result.blockers == []

    def test_gate_0_rejects_missing_rationale(self):
        """GATE_0 rejeita rationale ausente."""
        artifact_data = {
            "project": "proj",
            "demand": "feature",
            "mode": "FAST",
            "total_score": 5,
            "dimensions": {"impacto_arquitetural": 1},
            "rationale": "",  # vazio
            "override_applied": False,
            "classified_by": "intake-classifier",
            "timestamp": "2026-04-16T00:00:00Z",
        }

        gate_result = evaluate_gate("GATE_0", artifact_data)
        assert gate_result.state == "rejected"
        assert "rationale" in str(gate_result.blockers)

    def test_gate_0_rejects_invalid_mode(self):
        """GATE_0 rejeita modo inválido."""
        artifact_data = {
            "project": "proj",
            "demand": "feature",
            "mode": "INVALID",
            "total_score": 5,
            "dimensions": {"impacto_arquitetural": 1},
            "rationale": "some rationale",
            "override_applied": False,
            "classified_by": "intake-classifier",
            "timestamp": "2026-04-16T00:00:00Z",
        }

        gate_result = evaluate_gate("GATE_0", artifact_data)
        assert gate_result.state == "rejected"
        assert any("Modo inválido" in b for b in gate_result.blockers)

    def test_gate_0_rejects_missing_dimensions(self):
        """GATE_0 rejeita dimensions ausente."""
        artifact_data = {
            "project": "proj",
            "demand": "feature",
            "mode": "FAST",
            "total_score": 5,
            "dimensions": {},  # vazio
            "rationale": "some rationale",
            "override_applied": False,
            "classified_by": "intake-classifier",
            "timestamp": "2026-04-16T00:00:00Z",
        }

        gate_result = evaluate_gate("GATE_0", artifact_data)
        assert gate_result.state == "rejected"


class TestEndToEndClassificationContractGate:
    """Teste de integração completa: classify -> save -> validate -> gate."""

    def test_full_pipeline_classify_to_gate(self):
        """Fluxo completo: classificar, salvar, validar com contrato, avaliar gate."""
        dims = {
            "impacto_arquitetural": 2,
            "modulos_afetados": 1,
            "risco_de_regressao": 2,
            "criticidade_de_negocio": 1,
            "sensibilidade_de_dados": 1,
            "dependencia_externa": 1,
            "reversibilidade": 1,
            "complexidade_de_validacao": 1,
        }

        # 1. Classificar
        result = classify("demo-proj", "nova feature", dims, "demo classification")
        assert result.mode == "ENTERPRISE"

        # 2. Salvar
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "classification.json"
            save_classification(result, path)

            # 3. Carregar
            loaded = load_classification(path)
            loaded_data = loaded.to_dict()

            # 4. Validar contra contrato
            errors = validate_artifact("classification.json", loaded_data)
            assert errors == [], f"Contract validation errors: {errors}"

            # 5. Avaliar gate
            gate_result = evaluate_gate("GATE_0", loaded_data)
            assert gate_result.state == "approved"
            assert gate_result.gate == "GATE_0"
            assert gate_result.approver == "Intake Classifier"
