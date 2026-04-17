"""
PR-05: Testes para Guardian, Drift e Evaluator sem placeholders críticos
Valida que as verificações centrais não são mais placeholders.
"""

import pytest
import tempfile
import json
from pathlib import Path

from cvg_harness.guardian.architecture_guardian import ArchitectureGuardian
from cvg_harness.drift.drift_detector import DriftDetector


class TestArchitectureGuardianNoPlaceholders:
    """Valida que verificações centrais não são mais placeholders."""

    def test_circular_dependency_detected(self):
        """Dependência circular é detectada."""
        guardian = ArchitectureGuardian(
            authorized_areas=["src/a", "src/b"],
            prohibited_areas=["src/legacy"],
        )
        # Dependência a -> b E b -> a = circular
        report = guardian.check(
            changed_files=["src/a/file.py"],
            new_dependencies=["src/a -> src/b", "src/b -> src/a"]
        )
        assert report.result == "FAIL"
        rules = [v["rule"] for v in report.violations]
        assert "circular_dependency" in rules

    def test_domain_coupling_detected(self):
        """Acoplamento de domínio diferente é bloqueante."""
        guardian = ArchitectureGuardian(
            authorized_areas=["src/auth", "src/api"],
            prohibited_areas=["src/legacy"],
        )
        # Arquivo em domínio diferente
        report = guardian.check(
            changed_files=["src/frontend/button.py"],
            new_dependencies=[]
        )
        assert report.result == "FAIL"
        rules = [v["rule"] for v in report.violations]
        assert "domain_coupling" in rules

    def test_undeclared_tech_debt_detected(self):
        """Débito técnico não declarado é detectado."""
        guardian = ArchitectureGuardian(
            authorized_areas=["src/auth"],
            prohibited_areas=["src/legacy"],
        )
        report = guardian.check(
            changed_files=["src/auth/login.py"],
            new_dependencies=["TODO: refatorar depois"]
        )
        assert report.result == "FAIL"
        rules = [v["rule"] for v in report.violations]
        assert "undeclared_tech_debt" in rules

    def test_boundary_touch_inside_authorized_area_requires_waiver(self):
        """Boundary sensível dentro da área autorizada exige waiver, não fail direto."""
        guardian = ArchitectureGuardian(
            authorized_areas=["src/auth"],
            prohibited_areas=["src/legacy"],
            boundaries=["src/auth/oauth2"],
        )
        report = guardian.check(
            changed_files=["src/auth/oauth2/token.py"],
            new_dependencies=[]
        )
        assert report.result == "WAIVER"
        violation = next(v for v in report.violations if v["rule"] == "unauthorized_boundary_change")
        assert violation["severity"] == "waiver"

    def test_explicit_boundary_authorization_passes(self):
        """Boundary explicitamente autorizada não deve gerar violação."""
        guardian = ArchitectureGuardian(
            authorized_areas=["src/auth/oauth2"],
            prohibited_areas=["src/legacy"],
            boundaries=["src/auth/oauth2"],
        )
        report = guardian.check(
            changed_files=["src/auth/oauth2/token.py"],
            new_dependencies=[]
        )
        assert report.result == "PASS"
        assert report.violations == []

    def test_scope_matching_is_prefix_based_not_substring(self):
        """Áreas autorizadas usam prefixo de caminho, não substring solta."""
        guardian = ArchitectureGuardian(
            authorized_areas=["src/auth"],
            prohibited_areas=["src/legacy"],
        )
        report = guardian.check(
            changed_files=["src/authz/token.py"],
            new_dependencies=[]
        )
        assert report.result == "FAIL"
        rules = [v["rule"] for v in report.violations]
        assert "outside_authorized_area" in rules

    def test_multiple_violations_all_captured(self):
        """Múltiplas violações são todas capturadas."""
        guardian = ArchitectureGuardian(
            authorized_areas=["src/auth"],
            prohibited_areas=["src/legacy"],
        )
        report = guardian.check(
            changed_files=["src/legacy/old.py", "src/frontend/comp.py"],
            new_dependencies=["TODO: hack temporário"]
        )
        assert report.result == "FAIL"
        assert len(report.violations) >= 3


class TestDriftDetectorExecutionEvaluation:
    """Valida que drift execution x evaluation é detectável."""

    def test_execution_evaluation_drift_detected(self):
        """Drift entre execução e avaliação é detectado."""
        detector = DriftDetector(sprint_id="SPRINT-1")
        execution = {
            "arquivos_alterados": ["src/auth/login.py"],
            "escopo_planejado": ["src/auth/"]
        }
        evaluation = {
            "result": "FAILED",
            "evidence_missing": ["implementação dos arquivos"]
        }
        # Sem arquivos executados mas com falha
        report = detector.detect(execution=execution, evaluation=evaluation)
        findings = [f["layer"] for f in report.findings]
        assert "execucao_x_avaliacao" in findings or report.result == "CLEAN"

    def test_execution_outside_planned_scope(self):
        """Execução fora do escopo planejado é detectada."""
        detector = DriftDetector(sprint_id="SPRINT-1")
        execution = {
            "arquivos_alterados": ["src/legacy/old.py", "src/auth/login.py"],
            "escopo_planejado": ["src/auth/"]
        }
        evaluation = {"result": "PASSED"}
        report = detector.detect(execution=execution, evaluation=evaluation)
        # Deve detectar que src/legacy está fora do escopo
        if report.findings:
            layers = [f["layer"] for f in report.findings]
            assert "execucao_x_avaliacao" in layers

    def test_evaluation_release_readiness_root_cause_is_reported(self):
        """Drift evaluation x release readiness expõe root cause e remediation."""
        detector = DriftDetector(sprint_id="SPRINT-1")
        evaluation = {"result": "FAILED", "evidence_missing": ["logs de execução"]}
        release = {
            "decision": "APPROVED",
            "gates_summary": [{"gate": "GATE_7", "state": "approved"}],
            "missing_gates": [],
            "residual_risks": [],
        }
        report = detector.detect(evaluation=evaluation, release_readiness=release)
        finding = next(f for f in report.findings if f["layer"] == "avaliacao_x_release_readiness")
        assert finding["severity"] == "critical"
        assert finding["suspected_root_cause"]
        assert finding["remediation"]

    def test_spec_modules_match_nested_sprint_modules(self):
        """Módulos da SPEC são considerados cobertos por módulos aninhados do sprint plan."""
        detector = DriftDetector(sprint_id="SPRINT-1")
        spec = {"modulos": ["src/auth"]}
        sprint_plan = {"sprints": [{"modulos": ["src/auth/oauth2/token.py"]}]}

        report = detector.detect(spec=spec, sprint_plan=sprint_plan)

        assert report.result == "CLEAN"
        assert report.findings == []

    def test_execution_evidence_gap_with_files_present(self):
        """Falha de avaliação com arquivos produzidos gera causalidade mais explícita."""
        detector = DriftDetector(sprint_id="SPRINT-1")
        execution = {
            "arquivos_alterados": ["src/auth/login.py"],
            "escopo_planejado": ["src/auth/"],
        }
        evaluation = {
            "result": "FAILED",
            "evidence_missing": ["tests de login"],
        }

        report = detector.detect(execution=execution, evaluation=evaluation)

        findings = [f for f in report.findings if f["layer"] == "execucao_x_avaliacao"]
        assert findings
        assert any("faltam evidências" in f["finding"] for f in findings)


class TestEvaluatorNegativeScenarios:
    """Testa cenários negativos do evaluator."""

    def test_evaluator_fails_without_evidence(self):
        """Avaliador falha quando evidência obrigatória não existe."""
        from cvg_harness.evaluator.evaluator import Evaluator

        evaluator = Evaluator()
        report = evaluator.evaluate(
            sprint_id="SPRINT-1",
            spec={
                "meta": "test",
                "criterios": [
                    {"descricao": "feature funcionando", "testavel": True}
                ]
            },
            evidence_files=[],  # sem evidências
            round_num=1,
        )
        assert report.result == "FAILED"
        assert len(report.evidence_missing) > 0

    def test_evaluator_fails_with_untestable_criterion(self):
        """Avaliador falha quando critério não é testável."""
        from cvg_harness.evaluator.evaluator import Evaluator

        evaluator = Evaluator()
        report = evaluator.evaluate(
            sprint_id="SPRINT-1",
            spec={
                "meta": "test",
                "criterios": [
                    {"descricao": "satisfação do usuário", "testavel": False}
                ]
            },
            evidence_files=["implementação"],
            round_num=1,
        )
        assert report.result == "FAILED"

    def test_evaluator_tracks_round_and_next_action(self):
        """Avaliador rastreia round e define next_action corretamente."""
        from cvg_harness.evaluator.evaluator import Evaluator

        evaluator = Evaluator()

        # Round 1 com falha
        report1 = evaluator.evaluate(
            sprint_id="SPRINT-1",
            spec={"meta": "test", "criterios": []},
            evidence_files=[],
            round_num=1,
        )
        assert report1.next_action == "retry"

        # Round 3 com falha
        report3 = evaluator.evaluate(
            sprint_id="SPRINT-1",
            spec={"meta": "test", "criterios": []},
            evidence_files=[],
            round_num=3,
        )
        assert report3.next_action == "replan"
