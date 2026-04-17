"""
Testes para Evaluator e Release Readiness.
"""

import pytest
import tempfile
from pathlib import Path

from cvg_harness.gates.gate_policy import evaluate_gate
from cvg_harness.evaluator.evaluator import Evaluator, EvaluationReport, save_evaluation, load_evaluation
from cvg_harness.release.release_readiness import (
    ReleaseReadinessEngine, ReleaseReadiness, save_release_readiness, load_release_readiness
)
from cvg_harness.contracts.artifact_contracts import validate_artifact


def test_evaluator_passed():
    """Avaliação passa quando todos os critérios são testáveis e evidências presentes."""
    evaluator = Evaluator()
    spec = {
        "meta": "test feature",
        "criterios": [
            {"descricao": "API retorna 200", "testavel": True},
            {"descricao": "Erro retorna JSON", "testavel": True},
        ],
    }
    report = evaluator.evaluate("SPRINT-1", spec, ["implementação dos arquivos", "testes unitários", "logs de execução"])
    assert report.result == "PASSED"
    assert report.next_action == "none"


def test_evaluator_failed_missing_evidence():
    """Avaliação falha quando evidências estão faltando."""
    evaluator = Evaluator()
    spec = {
        "meta": "test",
        "criterios": [{"descricao": "teste", "testavel": True}],
    }
    report = evaluator.evaluate("SPRINT-1", spec, ["implementação"])
    assert report.result == "FAILED"
    assert len(report.evidence_missing) > 0


def test_evaluator_accepts_structured_evidence_payload():
    """Evaluator reconhece evidência estruturada com kind/ref/module."""
    evaluator = Evaluator()
    spec = {
        "meta": "test",
        "criterios": [{"descricao": "teste", "testavel": True}],
        "criterios_aceite": [
            {"descricao": "implementação auth", "kind": "implementation", "ref": "src/auth/login.py", "module": "auth"},
        ],
    }
    report = evaluator.evaluate(
        "SPRINT-1",
        spec,
        [
            {"kind": "implementation", "summary": "implementação auth", "ref": "src/auth/login.py", "module": "auth"},
            {"kind": "test", "summary": "testes auth", "ref": "tests/test_auth.py", "module": "auth"},
        ],
    )
    assert report.result == "PASSED"
    assert any(item.get("notes") == "evidência estruturada reconhecida" for item in report.criterion_results)
    assert report.structured_evidence_count == 2
    assert report.structured_evidence_summary[0]["kind"] == "implementation"
    assert report.status == "passed"
    assert report.criterios == report.criterion_results
    assert validate_artifact("evaluation-report.json", report.to_dict()) == []

def test_evaluator_structured_evidence_satisfies_expected_categories_without_legacy_text():
    """Kind/ref/module satisfazem evidências esperadas mesmo sem frases legadas."""
    evaluator = Evaluator()
    spec = {
        "meta": "test",
        "criterios": [{"descricao": "teste", "testavel": True}],
        "modulos": ["auth"],
        "criterios_aceite": [
            {"descricao": "patch auth aplicado", "kind": "implementation", "ref": "src/auth/login.py", "module": "auth"},
            {"descricao": "suite auth verde", "kind": "test", "ref": "tests/test_auth.py", "module": "auth"},
        ],
    }
    report = evaluator.evaluate(
        "SPRINT-1",
        spec,
        [
            {"kind": "implementation", "summary": "patchset #42", "ref": "src/auth/login.py", "module": "auth"},
            {"kind": "test", "summary": "pytest subset ok", "ref": "tests/test_auth.py", "module": "auth"},
            {"kind": "log", "summary": "trace run 2026-04-16", "ref": "logs/auth.log", "module": "auth"},
        ],
    )
    assert report.result == "PASSED"
    assert report.evidence_missing == []
    assert report.structured_evidence_count == 3


def test_evaluator_failed_unittable_criterion():
    """Avaliação falha quando critério não é testável."""
    evaluator = Evaluator()
    spec = {
        "meta": "test",
        "criterios": [{"descricao": "deve funcionar bem", "testavel": False}],
    }
    report = evaluator.evaluate("SPRINT-1", spec, ["implementação"])
    assert report.result == "FAILED"


def test_evaluator_treated_lacuna_as_waived():
    """Critério não testável com lacuna explícita não bloqueia se tiver marcação explícita."""
    evaluator = Evaluator()
    spec = {
        "meta": "test",
        "criterios": [
            {"descricao": "Feature implementada e funcionando", "testavel": False, "definido_como_lacuna": True},
        ],
    }
    report = evaluator.evaluate(
        "SPRINT-1",
        spec,
        ["implementação dos arquivos", "testes unitários", "logs de execução"],
    )
    assert report.result == "PASSED"
    assert any(item["status"] == "waived" for item in report.criterion_results)


def test_evaluator_failed_arch_guard():
    """Avaliação falha quando architecture guard reprova."""
    evaluator = Evaluator()
    spec = {"meta": "test", "criterios": [{"descricao": "teste", "testavel": True}]}
    guard_report = {"result": "FAIL", "violations": [{"rule": "prohibited_area_touched"}]}
    report = evaluator.evaluate("SPRINT-1", spec, ["implementação", "testes"], guard_report=guard_report)
    assert report.result == "FAILED"


def test_evaluator_round_tracking():
    """Round é incrementado corretamente."""
    evaluator = Evaluator()
    spec = {"meta": "test", "criterios": []}
    report = evaluator.evaluate("SPRINT-1", spec, [], round_num=2)
    assert report.round == 2


def test_evaluation_persistence():
    """Salva e carrega relatório de avaliação."""
    report = EvaluationReport(
        sprint_id="SPRINT-1",
        spec_ref="test",
        result="PASSED",
        criterion_results=[{"criterion": "teste", "status": "passed"}],
        evidence_provided=["impl", "testes"],
        evidence_missing=[],
        next_action="none",
    )
    report.criterios = report.criterion_results
    report.status = "passed"
    report.evidencias = [{"kind": "text", "ref": "impl", "module": ""}]
    report.falhas = []
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        path = Path(f.name)
    save_evaluation(report, path)
    loaded = load_evaluation(path)
    assert loaded.sprint_id == "SPRINT-1"
    assert loaded.result == "PASSED"
    assert loaded.status == "passed"
    path.unlink()


def test_release_readiness_approved():
    """Release aprovado quando todos os gates passaram."""
    engine = ReleaseReadinessEngine()
    gate_results = [
        {"gate": "GATE_0", "state": "approved", "blockers": []},
        {"gate": "GATE_1", "state": "approved", "blockers": []},
        {"gate": "GATE_2", "state": "approved", "blockers": []},
        {"gate": "GATE_3", "state": "approved", "blockers": []},
        {"gate": "GATE_4", "state": "approved", "blockers": []},
        {"gate": "GATE_5", "state": "approved", "blockers": []},
        {"gate": "GATE_6", "state": "approved", "blockers": []},
        {"gate": "GATE_7", "state": "approved", "blockers": []},
        {"gate": "GATE_8", "state": "approved", "blockers": []},
        {"gate": "GATE_9", "state": "approved", "blockers": []},
    ]
    evaluation = {"result": "PASSED"}
    drift = {"result": "CLEAN", "findings": []}

    report = engine.assess("proj", "feature", gate_results, evaluation, drift)
    assert report.decision == "APPROVED"


def test_release_readiness_rejected():
    """Release rejeitado quando há blockers."""
    engine = ReleaseReadinessEngine()
    gate_results = [
        {"gate": "GATE_7", "state": "rejected", "blockers": ["avaliação falhou"]},
    ]
    evaluation = {"result": "FAILED"}
    drift = {"result": "DRIFT_DETECTED", "findings": [{"severity": "high"}]}

    report = engine.assess("proj", "feature", gate_results, evaluation, drift)
    assert report.decision == "REJECTED"


def test_release_readiness_rejected_on_critical_drift():
    """Release rejeitado quando drift crítico está presente."""
    engine = ReleaseReadinessEngine()
    gate_results = [
        {"gate": "GATE_0", "state": "approved", "blockers": []},
        {"gate": "GATE_1", "state": "approved", "blockers": []},
        {"gate": "GATE_2", "state": "approved", "blockers": []},
        {"gate": "GATE_3", "state": "approved", "blockers": []},
        {"gate": "GATE_4", "state": "approved", "blockers": []},
        {"gate": "GATE_5", "state": "approved", "blockers": []},
        {"gate": "GATE_6", "state": "approved", "blockers": []},
        {"gate": "GATE_7", "state": "approved", "blockers": []},
        {"gate": "GATE_8", "state": "approved", "blockers": []},
        {"gate": "GATE_9", "state": "approved", "blockers": []},
    ]
    evaluation = {"result": "PASSED"}
    drift = {"result": "DRIFT_DETECTED", "findings": [{"severity": "critical"}]}

    report = engine.assess("proj", "feature", gate_results, evaluation, drift)
    assert report.decision == "REJECTED"
    assert "Drift de alta severidade detectado" in report.residual_risks


def test_release_readiness_conditional():
    """Release condicional quando há waivers."""
    engine = ReleaseReadinessEngine()
    gate_results = [
        {"gate": "GATE_0", "state": "approved", "blockers": []},
        {"gate": "GATE_1", "state": "approved", "blockers": []},
        {"gate": "GATE_2", "state": "approved", "blockers": []},
        {"gate": "GATE_3", "state": "approved", "blockers": []},
        {"gate": "GATE_4", "state": "approved", "blockers": []},
        {"gate": "GATE_5", "state": "waived", "blockers": ["waiver granted"]},
        {"gate": "GATE_6", "state": "approved", "blockers": []},
        {"gate": "GATE_7", "state": "approved", "blockers": []},
        {"gate": "GATE_8", "state": "approved", "blockers": []},
        {"gate": "GATE_9", "state": "approved", "blockers": []},
    ]
    evaluation = {"result": "PASSED"}
    drift = {"result": "CLEAN", "findings": []}

    report = engine.assess("proj", "feature", gate_results, evaluation, drift)
    assert report.decision == "CONDITIONAL"


def test_gate_8_blocks_critical_drift():
    """Gate 8 bloqueia drift crítico."""
    result = evaluate_gate(
        "GATE_8",
        {"result": "DRIFT_DETECTED", "findings": [{"severity": "critical"}]},
    )
    assert result.state == "rejected"
    assert result.blockers


def test_release_persistence():
    """Salva e carrega relatório de release."""
    readiness = ReleaseReadiness(
        project="proj",
        feature="feature",
        decision="APPROVED",
        gates_summary=[{"gate": "GATE_9", "state": "approved"}],
        missing_gates=[],
        exceptions=[],
        residual_risks=[],
        waivers=[],
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        path = Path(f.name)
    save_release_readiness(readiness, path)
    loaded = load_release_readiness(path)
    assert loaded.decision == "APPROVED"
    assert loaded.project == "proj"
    path.unlink()


def test_release_readiness_rejected_when_required_gate_missing():
    """Release rejeita quando GATE_6 ou GATE_8 estiver ausente."""
    engine = ReleaseReadinessEngine()
    gate_results = [
        {"gate": "GATE_0", "state": "approved", "blockers": []},
        {"gate": "GATE_1", "state": "approved", "blockers": []},
        {"gate": "GATE_2", "state": "approved", "blockers": []},
        {"gate": "GATE_3", "state": "approved", "blockers": []},
        {"gate": "GATE_4", "state": "approved", "blockers": []},
        {"gate": "GATE_5", "state": "approved", "blockers": []},
        {"gate": "GATE_7", "state": "approved", "blockers": []},
        {"gate": "GATE_9", "state": "approved", "blockers": []},
    ]
    evaluation = {"result": "PASSED"}
    drift = {"result": "CLEAN", "findings": []}

    report = engine.assess("proj", "feature", gate_results, evaluation, drift)
    assert report.decision == "REJECTED"
    assert "GATE_6" in report.missing_gates
    assert "GATE_8" in report.missing_gates
