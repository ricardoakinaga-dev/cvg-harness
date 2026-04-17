"""
Testes para Drift Detector.
"""

import pytest
from cvg_harness.drift.drift_detector import DriftDetector, DriftSeverity


def test_drift_clean():
    detector = DriftDetector(sprint_id="sprint-1")
    report = detector.detect()
    assert report.result == "CLEAN"
    assert report.findings == []


def test_drift_intake_prd_mismatch():
    detector = DriftDetector(sprint_id="sprint-1")
    intake = {"problema": "autenticação lenta"}
    prd = {"problema": "performance do dashboard"}
    report = detector.detect(intake=intake, prd=prd)
    assert report.result == "DRIFT_DETECTED"
    assert len(report.findings) > 0
    assert any(f["layer"] == "intake_x_prd" for f in report.findings)


def test_drift_prd_spec_mismatch():
    detector = DriftDetector(sprint_id="sprint-1")
    prd = {"objetivo": "melhorar performance"}
    spec = {"meta": "adicionar feature X"}
    report = detector.detect(prd=prd, spec=spec)
    assert report.result == "DRIFT_DETECTED"
    assert any(f["layer"] == "prd_x_spec" for f in report.findings)


def test_drift_spec_sprint_plan():
    detector = DriftDetector(sprint_id="sprint-1")
    spec = {"modulos": ["auth", "api", "db"]}
    sprint_plan = {
        "sprints": [
            {"modulos": ["auth"]},
        ]
    }
    report = detector.detect(spec=spec, sprint_plan=sprint_plan)
    assert report.result == "DRIFT_DETECTED"
    assert any(f["layer"] == "spec_x_sprint_plan" for f in report.findings)


def test_drift_sprint_plan_execution():
    detector = DriftDetector(sprint_id="sprint-1")
    sprint_plan = {"arquivos_esperados": ["a.py", "b.py"]}
    execution = {"arquivos_alterados": ["a.py", "b.py", "c.py"]}
    report = detector.detect(sprint_plan=sprint_plan, execution=execution)
    assert report.result == "DRIFT_DETECTED"
    assert any(f["layer"] == "sprint_plan_x_execucao" for f in report.findings)


def test_drift_execution_evaluation_passed_without_outputs():
    detector = DriftDetector(sprint_id="sprint-1")
    execution = {"arquivos_alterados": [], "escopo_planejado": ["src/auth/"]}
    evaluation = {"result": "PASSED", "evidence_missing": []}
    report = detector.detect(execution=execution, evaluation=evaluation)
    assert report.result == "DRIFT_DETECTED"
    finding = next(f for f in report.findings if f["layer"] == "execucao_x_avaliacao")
    assert finding["severity"] == DriftSeverity.MEDIUM.value
    assert "sem arquivos alterados" in finding["finding"].lower()
    assert finding["suspected_root_cause"]
    assert finding["remediation"]


def test_drift_evaluation_release_readiness_conflict():
    detector = DriftDetector(sprint_id="sprint-1")
    evaluation = {"result": "FAILED", "evidence_missing": ["testes unitários"]}
    release = {"decision": "APPROVED", "gates_summary": [{"gate": "GATE_7", "state": "approved"}], "missing_gates": [], "residual_risks": []}
    report = detector.detect(evaluation=evaluation, release_readiness=release)
    assert report.result == "DRIFT_DETECTED"
    layers = [f["layer"] for f in report.findings]
    assert "avaliacao_x_release_readiness" in layers
    critical = next(f for f in report.findings if f["finding"] == "Avaliação reprovou mas release readiness aprovou")
    assert critical["severity"] == DriftSeverity.CRITICAL.value
