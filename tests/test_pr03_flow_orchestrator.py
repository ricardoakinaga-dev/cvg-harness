"""
PR-03: Testes de fluxo fim a fim no orchestrator
Valida que o orchestrator coordena todas as fases
e gera eventos e handoffs corretamente.
"""

import pytest
import tempfile
import json
from pathlib import Path

from cvg_harness.flow import FlowOrchestrator


class TestFlowOrchestratorPhaseMethods:
    """Valida métodos explícitos para cada fase."""

    def setup_method(self):
        self.workspace = Path(tempfile.mkdtemp())
        self.orch = FlowOrchestrator("proj", "OAuth2 feature", "ENTERPRISE", self.workspace)
        dims = {"impacto_arquitetural": 2, "modulos_afetados": 1, "risco_de_regressao": 2,
                "criticidade_de_negocio": 1, "sensibilidade_de_dados": 1, "dependencia_externa": 1,
                "reversibilidade": 1, "complexidade_de_validacao": 1}
        self.orch.classify(dims, "critical feature")

    def test_run_research_generates_markdown_and_json(self):
        """run_research() gera research-notes.md e research-notes.json."""
        research_md, system_map_md = self.orch.run_research()

        assert Path(research_md).exists()
        assert Path(system_map_md).exists()
        assert (self.workspace / "artifacts" / "research-notes.md").exists()
        assert (self.workspace / "artifacts" / "research-notes.json").exists()
        assert (self.workspace / "artifacts" / "system-map.md").exists()
        assert (self.workspace / "artifacts" / "system-map.json").exists()

    def test_run_research_creates_handoff(self):
        """run_research() cria handoff."""
        self.orch.run_research()
        handoff_path = self.workspace / "artifacts" / "handoff-intake_to_research.json"
        assert handoff_path.exists()

    def test_run_research_generates_event(self):
        """run_research() gera evento research_approved."""
        self.orch.run_research()
        events = []
        with open(self.workspace / "event-log.jsonl") as f:
            for line in f:
                events.append(json.loads(line))
        assert any(e["event_type"] == "research_approved" for e in events)

    def test_classify_emits_causal_gate_event(self):
        """classify() também registra evento causal do gate com blockers e artefato de origem."""
        events = []
        with open(self.workspace / "event-log.jsonl") as f:
            for line in f:
                events.append(json.loads(line))
        gate_event = next(e for e in events if e["event_type"] == "gate_approved" and e["metadata"]["gate"] == "GATE_0")
        assert gate_event["metadata"]["state"] == "approved"
        assert gate_event["metadata"]["previous_state"] == "not_started"
        assert gate_event["metadata"]["source_artifact_ref"].endswith("classification.json")
        assert gate_event["metadata"]["blockers"] == []

    def test_run_research_uses_repository_evidence_when_available(self):
        """run_research() usa evidência do repositório quando o workspace não tem src local."""
        workspace = Path(tempfile.mkdtemp())
        orch = FlowOrchestrator("proj", "release readiness gates", "FAST", workspace)
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
        orch.classify(dims, "release flow")
        orch.run_research()

        with open(workspace / "artifacts" / "research-notes.json") as f:
            research = json.load(f)
        with open(workspace / "artifacts" / "system-map.json") as f:
            system_map = json.load(f)

        assert "release" in research["modulos_impactados"]
        assert any(module in system_map["modulos"] for module in ["release", "gates"])
        assert any("Code root observado" in fato for fato in research["fatos"])

    def test_run_prd_generates_prd_md(self):
        """run_prd() gera prd.md."""
        self.orch.run_research()
        prd_md = self.orch.run_prd()

        assert Path(prd_md).exists()
        assert (self.workspace / "artifacts" / "prd.md").exists()
        assert (self.workspace / "artifacts" / "prd.json").exists()
        content = Path(prd_md).read_text()
        assert "# PRD:" in content

    def test_run_prd_updates_state(self):
        """run_prd() atualiza estado e gate."""
        self.orch.run_research()
        prd_md = self.orch.run_prd()

        assert self.orch.state.current_gate == "GATE_2"
        assert self.orch.state.current_phase == "prd"
        assert self.orch.state.prd_path is not None

    def test_build_spec_generates_markdown_and_json(self):
        """build_spec() gera spec.md e spec.json."""
        self.orch.run_research()
        self.orch.run_prd()
        spec_md, spec_json = self.orch.build_spec()

        assert Path(spec_md).exists()
        assert Path(spec_json).exists()
        assert (self.workspace / "artifacts" / "spec.md").exists()
        assert (self.workspace / "artifacts" / "spec.json").exists()

    def test_build_spec_synchronized_version(self):
        """spec.md e spec.json compartilham versão."""
        self.orch.run_research()
        self.orch.run_prd()
        spec_md, spec_json = self.orch.build_spec()

        with open(spec_json) as f:
            spec_data = json.load(f)
        md_content = Path(spec_md).read_text()
        assert spec_data["version"] in md_content

    def test_build_spec_reflects_real_workspace_context(self):
        """build_spec() reflete módulos reais do workspace em contratos e critérios."""
        workspace = Path(tempfile.mkdtemp())
        (workspace / "src").mkdir()
        (workspace / "src" / "auth").mkdir(parents=True)
        (workspace / "src" / "auth" / "session.py").write_text("def session_ok():\n    return True\n")
        (workspace / "src" / "api").mkdir(parents=True)
        (workspace / "src" / "api" / "handlers.py").write_text("def handler():\n    return 'ok'\n")

        orch = FlowOrchestrator("proj", "melhorar auth api", "ENTERPRISE", workspace)
        dims = {
            "impacto_arquitetural": 2,
            "modulos_afetados": 2,
            "risco_de_regressao": 2,
            "criticidade_de_negocio": 1,
            "sensibilidade_de_dados": 1,
            "dependencia_externa": 1,
            "reversibilidade": 1,
            "complexidade_de_validacao": 1,
        }
        orch.classify(dims, "auth api feature")
        orch.run_research()
        orch.run_prd()
        _, spec_json = orch.build_spec()

        with open(spec_json) as f:
            spec = json.load(f)

        assert any(mod in spec["modulos"] for mod in ["auth", "api"])
        assert any(area.startswith("src/auth") for area in spec["areas_autorizadas"])
        assert spec["contratos"], "espera contratos derivados do contexto real"
        assert any(c.get("criticidade") == "high" for c in spec["contratos"])
        assert any(c.get("superficie") in {"auth", "api"} for c in spec["contratos"])
        assert "logs estruturados de auth" in spec["observabilidade"]
        assert "sessões" in spec["rollback"].lower()
        assert any(c.get("definido_como_lacuna") for c in spec["criterios"])

    def test_plan_sprints_generates_sprint_plan(self):
        """plan_sprints() gera sprint-plan.json e execution-order.json."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        sprint_plan_path = self.orch.plan_sprints()

        assert Path(sprint_plan_path).exists()
        assert (self.workspace / "artifacts" / "sprint-plan.json").exists()

    def test_plan_sprints_generates_execution_order(self):
        """plan_sprints() também persiste execution-order.json."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.plan_sprints()

        exec_order_path = self.workspace / "artifacts" / "execution-order.json"
        assert exec_order_path.exists(), "execution-order.json should be generated"

        with open(exec_order_path) as f:
            exec_order = json.load(f)
        assert "sequencia" in exec_order
        assert "sprint_ids" in exec_order
        assert isinstance(exec_order["sequencia"], list)


    def test_check_guard_emits_architecture_guard_event(self):
        """check_guard() registra evento explícito de guard."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.plan_sprints()
        self.orch.check_guard(["src/auth/oauth2/token.py"])

        events = []
        with open(self.workspace / "event-log.jsonl") as f:
            for line in f:
                events.append(json.loads(line))
        event_types = [e["event_type"] for e in events]
        assert "architecture_guard_passed" in event_types

    def test_check_guard_boundary_touch_emits_waiver_event(self):
        """Boundary sensível dentro do escopo autorizado gera waiver explícito."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.plan_sprints()

        spec_path = self.workspace / "artifacts" / "spec.json"
        with open(spec_path) as f:
            spec = json.load(f)
        spec["areas_autorizadas"] = ["src/auth"]
        spec["areas_proibidas"] = ["src/legacy"]
        spec["boundaries"] = ["src/auth/oauth2"]
        with open(spec_path, "w") as f:
            json.dump(spec, f, indent=2)

        result = self.orch.check_guard(["src/auth/oauth2/token.py"])
        assert result["result"] == "WAIVER"

        events = []
        with open(self.workspace / "event-log.jsonl") as f:
            for line in f:
                events.append(json.loads(line))
        event_types = [e["event_type"] for e in events]
        assert "architecture_guard_waived" in event_types

    def test_check_guard_emits_causal_gate_metadata(self):
        """check_guard() registra gate causal com motivo, transição e artefato de origem."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.plan_sprints()

        spec_path = self.workspace / "artifacts" / "spec.json"
        with open(spec_path) as f:
            spec = json.load(f)
        spec["areas_autorizadas"] = ["src/auth"]
        spec["areas_proibidas"] = ["src/legacy"]
        spec["boundaries"] = ["src/auth/oauth2"]
        with open(spec_path, "w") as f:
            json.dump(spec, f, indent=2)

        self.orch.check_guard(["src/auth/oauth2/token.py"])

        events = []
        with open(self.workspace / "event-log.jsonl") as f:
            for line in f:
                events.append(json.loads(line))
        gate_event = next(e for e in events if e["event_type"] == "gate_waived" and e["metadata"]["gate"] == "GATE_6")
        assert gate_event["metadata"]["previous_state"] == "not_started"
        assert gate_event["metadata"]["source_artifact_ref"].endswith("architecture-guard-report.json")
        assert gate_event["metadata"]["blockers"] == []
        assert gate_event["metadata"]["state"] == "waived"

    def test_detect_drift_emits_drift_event(self):
        """detect_drift() registra drift_clean/drift_detected no event log."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.plan_sprints()
        self.orch.detect_drift()

        events = []
        with open(self.workspace / "event-log.jsonl") as f:
            for line in f:
                events.append(json.loads(line))
        event_types = [e["event_type"] for e in events]
        assert any(et in ("drift_clean", "drift_detected") for et in event_types)

    def test_detect_drift_emits_causal_gate_event(self):
        """detect_drift() também registra gate causal com severidade e artefato de origem."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.plan_sprints()
        self.orch.detect_drift()

        events = []
        with open(self.workspace / "event-log.jsonl") as f:
            for line in f:
                events.append(json.loads(line))
        gate_event = next(e for e in events if e["metadata"].get("gate") == "GATE_8")
        assert gate_event["event_type"] in {"gate_approved", "gate_rejected"}
        assert gate_event["metadata"]["source_artifact_ref"].endswith("drift-report.json")
        assert gate_event["metadata"]["output_artifact"] == "drift-report.json"

    def test_detect_drift_loads_evaluation_and_release_when_available(self):
        """detect_drift() usa evaluation-report e release readiness persistidos quando existirem."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.run_lint()
        self.orch.plan_sprints()
        self.orch.check_guard(["src/auth/oauth2/token.py"])

        eval_path = self.workspace / "reports" / "evaluation-report.json"
        with open(eval_path, "w") as f:
            json.dump({
                "sprint_id": "SPRINT-1",
                "spec_ref": "meta",
                "result": "FAILED",
                "criterion_results": [],
                "evidence_provided": [],
                "evidence_missing": ["logs de execução"],
                "next_action": "retry",
                "round": 1,
                "timestamp": "2026-04-16T00:00:00+00:00",
            }, f, indent=2)

        release_path = self.workspace / "reports" / "release-readiness-report.json"
        with open(release_path, "w") as f:
            json.dump({
                "project": "proj",
                "feature": "feature",
                "decision": "APPROVED",
                "gates_summary": [{"gate": "GATE_7", "state": "approved"}],
                "missing_gates": [],
                "exceptions": [],
                "residual_risks": [],
                "waivers": [],
                "timestamp": "2026-04-16T00:00:00+00:00",
            }, f, indent=2)

        result = self.orch.detect_drift()
        assert result["result"] == "DRIFT_DETECTED"
        layers = [finding["layer"] for finding in result["findings"]]
        assert "avaliacao_x_release_readiness" in layers

        events = []
        with open(self.workspace / "event-log.jsonl") as f:
            for line in f:
                events.append(json.loads(line))
        drift_event = next(e for e in reversed(events) if e["event_type"] == "drift_detected")
        assert drift_event["metadata"]["findings"] >= 1

    def test_evaluate_sprint_generates_report(self):
        """evaluate_sprint() gera evaluation-report.json."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.plan_sprints()

        evidence_files = ["implementação dos arquivos", "testes unitários", "logs de execução"]
        result = self.orch.evaluate_sprint(evidence_files)

        assert "result" in result
        report_path = self.workspace / "reports" / "evaluation-report.json"
        assert report_path.exists()

    def test_release_readiness_completes_flow_and_syncs_progress(self):
        """Release aprovado encerra o fluxo e sincroniza progress.json."""
        self.orch.run_research()
        self.orch.run_prd()
        self.orch.build_spec()
        self.orch.run_lint()
        self.orch.plan_sprints()
        self.orch.check_guard(["src/auth/oauth2/token.py"])
        self.orch.detect_drift()

        evidence_files = [
            "implementação dos arquivos",
            "testes unitários",
            "logs de execução",
            "implementação do módulo auth",
            "testes do módulo auth",
        ]
        self.orch.evaluate_sprint(evidence_files)
        result = self.orch.check_release_readiness()

        assert result["decision"] == "APPROVED"
        assert self.orch.state.current_phase == "release"
        assert self.orch.state.current_gate == "GATE_9"
        assert self.orch.state.status == "completed"

        with open(self.workspace / "progress.json") as f:
            progress = json.load(f)
        assert progress["current_gate"] == "GATE_9"
        assert progress["status"] == "completed"


class TestFlowOrchestratorProgressSync:
    """Valida que progress.json é sincronizado ao longo do fluxo."""

    def setup_method(self):
        self.workspace = Path(tempfile.mkdtemp())
        self.orch = FlowOrchestrator("proj", "feature", "FAST", self.workspace)
        dims = {"impacto_arquitetural": 1, "modulos_afetados": 1, "risco_de_regressao": 1,
                "criticidade_de_negocio": 0, "sensibilidade_de_dados": 0, "dependencia_externa": 0,
                "reversibilidade": 1, "complexidade_de_validacao": 1}
        self.orch.classify(dims, "simple feature")

    def test_sync_progress_after_classify(self):
        """progress.json é sincronizado após classify."""
        progress_path = self.orch.sync_progress()
        assert Path(progress_path).exists()

        with open(progress_path) as f:
            progress = json.load(f)
        assert progress["mode"] == "FAST"
        assert progress["current_gate"] == "GATE_0"

    def test_sync_progress_after_research(self):
        """progress.json é sincronizado após research."""
        self.orch.run_research()
        self.orch.sync_progress()

        progress_path = self.workspace / "progress.json"
        with open(progress_path) as f:
            progress = json.load(f)
        assert progress["current_gate"] == "GATE_1"


class TestFlowOrchestratorSingleSprintRule:
    """Valida que uma sprint ativa por fluxo é enforced."""

    def test_single_sprint_id_is_set(self):
        """Sprint ID único é configurado após plan_sprints."""
        workspace = Path(tempfile.mkdtemp())
        orch = FlowOrchestrator("proj", "feature", "FAST", workspace)
        dims = {"impacto_arquitetural": 1, "modulos_afetados": 1, "risco_de_regressao": 1,
                "criticidade_de_negocio": 0, "sensibilidade_de_dados": 0, "dependencia_externa": 0,
                "reversibilidade": 1, "complexidade_de_validacao": 1}
        orch.classify(dims, "simple")
        orch.run_research()
        orch.run_prd()
        orch.build_spec()
        orch.plan_sprints()

        assert orch.state.sprint_id != ""
        assert orch.state.sprint_id.startswith("SPRINT-")
