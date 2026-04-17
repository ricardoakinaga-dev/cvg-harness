"""
Testes de integração - fluxo completo do CVG Harness.
"""

import pytest
import tempfile
import json
from pathlib import Path

from cvg_harness.flow import FlowOrchestrator
from cvg_harness.ledger.progress_ledger import load_progress
from cvg_harness.ledger.event_log import load_events


def test_full_flow_fast_mode():
    """Testa fluxo completo em modo FAST."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # 1. Init
        orch = FlowOrchestrator("proj-x", "adição de campo", "FAST", workspace)
        assert orch.state.mode == "FAST"
        assert orch.state.current_phase == "intake"

        # 2. Classify
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
        class_path = orch.classify(dims, "mudança local")
        assert Path(class_path).exists()

        # 3. Check classification content
        with open(class_path) as f:
            classification = json.load(f)
        assert classification["mode"] == "FAST"
        assert classification["total_score"] <= 8

        # 4. Verify event log
        events = load_events(workspace / "event-log.jsonl")
        assert len(events) == 3
        assert events[0].event_type == "demand_received"
        assert events[1].event_type == "gate_approved"
        assert events[1].metadata["gate"] == "GATE_0"
        assert events[1].metadata["source_artifact_ref"].endswith("classification.json")
        assert events[2].event_type == "demand_classified"

        # 5. Advance phase
        orch.advance_phase("spec")
        assert orch.state.current_phase == "spec"

        # 6. Block and unblock
        orch.block("spec_incomplete")
        assert orch.state.status == "blocked"
        assert "spec_incomplete" in orch.state.blockers

        orch.state.blockers.remove("spec_incomplete")
        orch.state.status = "running"
        orch._save_state()
        assert orch.state.status == "running"


def test_full_flow_enterprise_mode():
    """Testa fluxo completo em modo ENTERPRISE."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        orch = FlowOrchestrator("proj-y", "novo fluxo de auth", "ENTERPRISE", workspace)
        assert orch.state.mode == "ENTERPRISE"

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
        class_path = orch.classify(dims, "autenticação crítica")
        with open(class_path) as f:
            classification = json.load(f)
        assert classification["mode"] == "ENTERPRISE"
        assert classification["total_score"] >= 9


def test_flow_with_guard_check():
    """Testa verificação de guard no fluxo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        orch = FlowOrchestrator("proj-z", "feature", "FAST", workspace)

        # Setup spec with authorized/prohibited areas
        spec_path = workspace / "artifacts" / "spec.json"
        spec = {
            "version": "v1",
            "meta": "test",
            "modulos": ["auth"],
            "areas_autorizadas": ["src/auth"],
            "areas_proibidas": ["src/legacy"],
            "criterios": [],
            "edge_cases": [],
            "contratos": [],
            "limite_escopo": "auth",
            "fluxo_critico": False,
            "rollback": "revert",
            "observabilidade": "logs",
        }
        with open(spec_path, "w") as f:
            json.dump(spec, f)
        orch.state.spec_path = str(spec_path)

        # Check with file in authorized area
        result = orch.check_guard(["src/auth/login.py"])
        assert result["result"] == "PASS"

        # Check with file in prohibited area
        result = orch.check_guard(["src/legacy/old.py"])
        assert result["result"] == "FAIL"
        assert any(v["rule"] == "prohibited_area_touched" for v in result["violations"])


def test_flow_drift_detection():
    """Testa detecção de drift no fluxo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        orch = FlowOrchestrator("proj-w", "feature", "FAST", workspace)

        # Create mismatched intake and prd
        intake_data = {"problema": "performance ruim"}
        prd_data = {"problema": "precisamos de mais features"}

        intake_path = workspace / "artifacts" / "intake.json"
        prd_path = workspace / "artifacts" / "prd.json"

        with open(intake_path, "w") as f:
            json.dump(intake_data, f)
        with open(prd_path, "w") as f:
            json.dump(prd_data, f)

        orch.state.classification_path = str(intake_path)
        orch.state.prd_path = str(prd_path)

        result = orch.detect_drift()
        assert result["result"] == "DRIFT_DETECTED"
        assert any(f["layer"] == "intake_x_prd" for f in result["findings"])


def test_flow_save_and_resume():
    """Testa persistência e retomada do fluxo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)

        # Create and modify
        orch1 = FlowOrchestrator("proj-v", "feature", "FAST", workspace)
        orch1.advance_phase("lint")
        orch1.block("arch_guard")
        orch1.state.sprint_id = "SPRINT-1"
        orch1._save_state()

        # Resume
        orch2 = FlowOrchestrator.load(workspace)
        assert orch2.state.current_phase == "lint"
        assert orch2.state.blockers == ["arch_guard"]
        assert orch2.state.sprint_id == "SPRINT-1"
        assert orch2.state.mode == "FAST"


def test_flow_progress_ledger_integration():
    """Testa integração do flow com progress ledger."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        orch = FlowOrchestrator("proj-u", "feature", "FAST", workspace)

        # Create progress via orchestrator
        dims = {"impacto_arquitetural": 1}
        orch.classify(dims, "test")

        # Verify flow-state.json exists (orchestrator uses flow-state, not progress)
        flow_state_path = workspace / "flow-state.json"
        assert flow_state_path.exists()

        # Verify event log was created
        event_log_path = workspace / "event-log.jsonl"
        assert event_log_path.exists()

        events = load_events(event_log_path)
        assert len(events) >= 1


def test_release_approved_completes_flow_and_progress():
    """Fluxo aprovado termina com state/progress coerentes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        orch = FlowOrchestrator("proj-release", "adição de autenticação OAuth2", "ENTERPRISE", workspace)

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
        orch.classify(dims, "autenticação crítica")
        orch.run_research()
        orch.run_prd()
        orch.build_spec()
        orch.run_lint()
        orch.plan_sprints()
        orch.check_guard(["src/auth/oauth2/token.py"])
        orch.detect_drift()
        orch.evaluate_sprint([
            "implementação dos arquivos",
            "testes unitários",
            "logs de execução",
            "implementação do módulo auth",
            "testes do módulo auth",
        ])

        result = orch.check_release_readiness()
        assert result["decision"] == "APPROVED"
        assert orch.state.status == "completed"
        assert orch.state.current_phase == "release"
        assert orch.state.current_gate == "GATE_9"

        with open(workspace / "flow-state.json") as f:
            flow_state = json.load(f)
        with open(workspace / "progress.json") as f:
            progress = json.load(f)

        assert flow_state["status"] == "completed"
        assert flow_state["current_phase"] == "release"
        assert progress["status"] == "completed"
        assert progress["current_gate"] == "GATE_9"


def test_flow_guard_and_drift_emit_canonical_events():
    """Guard e drift devem deixar trilha explícita no event log."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        orch = FlowOrchestrator("proj-events", "oauth2 auth", "ENTERPRISE", workspace)

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
        orch.classify(dims, "autenticação crítica")
        orch.run_research()
        orch.run_prd()
        orch.build_spec()
        orch.plan_sprints()
        orch.check_guard(["src/auth/oauth2/token.py"])
        orch.detect_drift()

        events = load_events(workspace / "event-log.jsonl")
        event_types = [e.event_type for e in events]
        assert "architecture_guard_passed" in event_types
        assert any(et in ("drift_clean", "drift_detected") for et in event_types)
