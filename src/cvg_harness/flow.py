"""
Flow Orchestrator - Orquestra o fluxo completo do CVG Harness.
Conecta Intake → Classification → SPEC → Sprint → Evaluation → Release.
"""

from __future__ import annotations

import json
import inspect
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class FlowState:
    """Estado do fluxo em um momento específico."""
    project: str
    feature: str
    mode: str
    current_gate: str
    current_phase: str  # intake | classification | research | prd | spec | lint | sprint | evaluation | release
    status: str  # running | blocked | completed | failed
    sprint_id: str = ""
    classification_path: Optional[str] = None
    prd_path: Optional[str] = None
    spec_path: Optional[str] = None
    sprint_plan_path: Optional[str] = None
    blockers: list[str] = field(default_factory=list)
    last_event: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class FlowOrchestrator:
    """
    Orquestra a execução do fluxo completo.
    Gerencia transições de fase, gates, eventos e estado.
    """

    def __init__(self, project: str, feature: str, mode: str, workspace: Path, context_workspace: Optional[Path] = None):
        self.project = project
        self.feature = feature
        self.mode = mode
        self.workspace = workspace
        self.context_workspace = context_workspace or workspace
        self.state = FlowState(
            project=project,
            feature=feature,
            mode=mode,
            current_gate="GATE_0",
            current_phase="intake",
            status="running",
        )
        self._setup_workspace()

    def _setup_workspace(self) -> None:
        self.workspace.mkdir(parents=True, exist_ok=True)
        (self.workspace / "artifacts").mkdir(exist_ok=True)
        (self.workspace / "reports").mkdir(exist_ok=True)
        (self.workspace / "reports" / "gates").mkdir(exist_ok=True)
        self.artifacts_dir = self.workspace / "artifacts"
        self.reports_dir = self.workspace / "reports"
        self.gates_dir = self.reports_dir / "gates"

    def _evaluate_and_save_gate(
        self,
        gate_name: str,
        artifact_data: dict,
        source_artifact_ref: str = "",
    ) -> "GateResult":
        """Avalia gate formalmente, persiste o resultado e registra evento causal."""
        from cvg_harness.gates.gate_policy import GATES as GATE_DEFS, evaluate_gate, save_gate_result
        from cvg_harness.types import GateState

        gate_file_name = f"gate-{gate_name}.json"
        gate_report_path = self.gates_dir / gate_file_name

        previous_state = GateState.NOT_STARTED.value
        if gate_report_path.exists():
            with open(gate_report_path) as f:
                previous_state = json.load(f).get("state", GateState.NOT_STARTED.value)

        gate_result = evaluate_gate(gate_name, artifact_data)
        save_gate_result(gate_result, gate_report_path)

        event_type_map = {
            GateState.APPROVED.value: "gate_approved",
            GateState.REJECTED.value: "gate_rejected",
            GateState.WAIVED.value: "gate_waived",
            GateState.IN_REVIEW.value: "gate_in_review",
        }
        gate_def = GATE_DEFS.get(gate_name, {})
        event_type = event_type_map.get(gate_result.state, "gate_in_review")
        self._append_event(
            event_type,
            gate_result.approver,
            str(gate_report_path),
            metadata={
                "gate": gate_name,
                "state": gate_result.state,
                "previous_state": previous_state,
                "blockers": gate_result.blockers,
                "source_artifact_ref": source_artifact_ref,
                "current_phase": self.state.current_phase,
                "objective": gate_def.get("objective", ""),
                "output_artifact": gate_def.get("output_artifact", ""),
            },
        )
        return gate_result

    def classify(self, dimensions: dict, rationale: str) -> str:
        """Executa classificação e salva artifact."""
        from cvg_harness.classification.classifier import classify, save_classification

        self._append_event("demand_received", "FlowOrchestrator", self.feature)
        result = classify(
            project=self.project,
            demand=self.feature,
            dimensions=dimensions,
            rationale=rationale,
        )
        path = self.artifacts_dir / "classification.json"
        save_classification(result, path)

        # Avaliação formal de GATE_0
        gate_result = self._evaluate_and_save_gate("GATE_0", result.to_dict(), str(path))

        self.state.classification_path = str(path)
        self.state.current_gate = "GATE_0"
        self.state.current_phase = "classification"
        self.state.last_event = "demand_classified"
        if gate_result.state == "rejected":
            self.state.status = "blocked"
            self.state.blockers.append("gate_0_rejected")
        self._save_state()
        self._append_event("demand_classified", "intake-classifier", str(path))
        return str(path)

    def run_lint(self) -> dict:
        """Executa spec linter no spec.json atual."""
        from cvg_harness.linter.spec_linter import lint_spec, save_lint_report

        if not self.state.spec_path:
            return {"result": "ERROR", "reason": "spec.json not found"}

        with open(self.state.spec_path) as f:
            spec = json.load(f)

        report = lint_spec(spec, mode=self.mode)
        report_path = self.reports_dir / "spec-lint-report.json"
        save_lint_report(report, report_path)
        self.state.current_gate = "GATE_4"

        # Avaliação formal de GATE_4
        gate_result = self._evaluate_and_save_gate("GATE_4", report.to_dict(), str(report_path))

        if report.result == "FAIL" or gate_result.state == "rejected":
            self.state.last_event = "spec_lint_failed"
            self.state.status = "blocked"
            if "spec_lint_failed" not in self.state.blockers:
                self.state.blockers.append("spec_lint_failed")
            # Integrar com FallbackPolicy
            self._handle_lint_failure()
        else:
            self.state.last_event = "spec_lint_passed"
            if "spec_lint_failed" in self.state.blockers:
                self.state.blockers.remove("spec_lint_failed")

        self._save_state()
        self._append_event(self.state.last_event, "Spec Linter", str(report_path))
        return report.to_dict()

    def _handle_lint_failure(self) -> None:
        """Processa falha do lint usando FallbackPolicy."""
        from cvg_harness.fallback.fallback_policy import FallbackPolicy, save_fallback_event

        policy = FallbackPolicy()
        fallback = policy.evaluate_spec_lint_failure()

        fallback_path = self.artifacts_dir / "fallback-events.jsonl"
        save_fallback_event(fallback, fallback_path)

    def check_guard(self, changed_files: list[str]) -> dict:
        """Verifica aderência arquitetural."""
        from cvg_harness.guardian.architecture_guardian import ArchitectureGuardian, save_guard_report

        if not self.state.spec_path:
            return {"result": "ERROR", "reason": "spec.json not found"}

        with open(self.state.spec_path) as f:
            spec = json.load(f)

        authorized = spec.get("areas_autorizadas", [])
        prohibited = spec.get("areas_proibidas", [])
        # boundaries: áreas declaradas na SPEC como needing special attention
        # Usa spec.json ou herda de research-notes via spec se disponível
        boundaries = spec.get("boundaries", [])

        guardian = ArchitectureGuardian(
            authorized_areas=authorized,
            prohibited_areas=prohibited,
            boundaries=boundaries,
        )
        report = guardian.check(changed_files=changed_files)

        report_path = self.reports_dir / f"architecture-guard-report.json"
        save_guard_report(report, report_path)

        if report.result == "FAIL":
            self.state.last_event = "architecture_guard_failed"
            self.state.status = "blocked"
            if "architecture_guard_failed" not in self.state.blockers:
                self.state.blockers.append("architecture_guard_failed")
            # Integrar com FallbackPolicy
            self._handle_guard_failure()
        elif report.result == "WAIVER":
            self.state.last_event = "architecture_guard_waived"
            if "architecture_guard_failed" in self.state.blockers:
                self.state.blockers.remove("architecture_guard_failed")
        else:
            self.state.last_event = "architecture_guard_passed"
            if "architecture_guard_failed" in self.state.blockers:
                self.state.blockers.remove("architecture_guard_failed")

        # Avaliação formal de GATE_6
        gate_result = self._evaluate_and_save_gate("GATE_6", report.to_dict(), str(report_path))
        self.state.current_gate = "GATE_6"

        self._save_state()
        self._append_event(
            self.state.last_event,
            "Architecture Guardian",
            str(report_path),
            metadata={
                "result": report.result,
                "violations": len(report.violations),
                "rules": [violation["rule"] for violation in report.violations],
            },
        )
        self.sync_progress()
        return report.to_dict()

    def _handle_guard_failure(self) -> None:
        """Processa falha do guard usando FallbackPolicy."""
        from cvg_harness.fallback.fallback_policy import FallbackPolicy, save_fallback_event

        policy = FallbackPolicy()
        fallback = policy.evaluate_arch_guard_failure()

        fallback_path = self.artifacts_dir / "fallback-events.jsonl"
        save_fallback_event(fallback, fallback_path)

        if fallback.action == "block":
            self.state.status = "blocked"

    def detect_drift(self) -> dict:
        """Detecta drift entre camadas."""
        from cvg_harness.drift.drift_detector import DriftDetector, save_drift_report

        intake = prd = spec = sprint_plan = evaluation = None
        if self.state.classification_path:
            with open(self.state.classification_path) as f:
                intake = json.load(f)
        if self.state.prd_path:
            with open(self.state.prd_path) as f:
                prd = json.load(f)
        if self.state.spec_path:
            with open(self.state.spec_path) as f:
                spec = json.load(f)
        if self.state.sprint_plan_path:
            with open(self.state.sprint_plan_path) as f:
                sprint_plan = json.load(f)

        evaluation_path = self.reports_dir / "evaluation-report.json"
        if evaluation_path.exists():
            with open(evaluation_path) as f:
                evaluation = json.load(f)

        detector = DriftDetector(sprint_id=self.state.sprint_id or self.feature)

        # Carregar release readiness se existir para verificar avaliação x release
        release_readiness = None
        rr_path = self.reports_dir / "release-readiness-report.json"
        if rr_path.exists():
            with open(rr_path) as f:
                release_readiness = json.load(f)

        report = detector.detect(
            intake=intake,
            prd=prd,
            spec=spec,
            sprint_plan=sprint_plan,
            evaluation=evaluation,
            release_readiness=release_readiness,
        )

        report_path = self.reports_dir / "drift-report.json"
        save_drift_report(report, report_path)
        self.state.last_event = "drift_detected" if report.result == "DRIFT_DETECTED" else "drift_clean"
        # Avaliação formal de GATE_8
        gate_result = self._evaluate_and_save_gate("GATE_8", report.to_dict(), str(report_path))
        self.state.current_gate = "GATE_8"
        if gate_result.state == "rejected":
            self.state.status = "blocked"
            self.state.blockers.append("gate_8_rejected")
        self._save_state()
        findings = report.findings if isinstance(report.findings, list) else []
        severities = [finding.get("severity") for finding in findings if isinstance(finding, dict)]
        self._append_event(
            self.state.last_event,
            "Drift Detector",
            str(report_path),
            metadata={
                "result": report.result,
                "layers_checked": report.layers_checked,
                "findings": len(findings),
                "highest_severity": severities[0] if severities else None,
            },
        )
        self.sync_progress()
        return report.to_dict()

    def run_research(self) -> tuple[str, str]:
        """Executa Research Agent e gera research-notes.md e system-map.md."""
        from cvg_harness.research.research_agent import (
            ResearchAgent, save_research, save_system_map,
            save_research_markdown, save_system_map_markdown
        )

        if not self.state.classification_path:
            raise ValueError("classification.json required before research")

        with open(self.state.classification_path) as f:
            classification = json.load(f)

        self._append_event("research_started", "FlowOrchestrator", self.state.classification_path)
        agent = ResearchAgent()
        research, system_map = agent.investigate(
            self.project,
            self.feature,
            classification,
            workspace=self.context_workspace,
        )

        # Salva JSON
        research_path = self.artifacts_dir / "research-notes.json"
        system_map_path = self.artifacts_dir / "system-map.json"
        save_research(research, research_path)
        save_system_map(system_map, system_map_path)

        # Salva Markdown
        research_md_path = self.artifacts_dir / "research-notes.md"
        system_map_md_path = self.artifacts_dir / "system-map.md"
        save_research_markdown(research, research_md_path)
        save_system_map_markdown(system_map, system_map_md_path)

        self.state.current_gate = "GATE_1"
        self.state.current_phase = "research"
        self.state.last_event = "research_approved"
        # Avaliação formal de GATE_1
        gate_result = self._evaluate_and_save_gate("GATE_1", research.to_dict(), str(research_path))
        if gate_result.state == "rejected":
            self.state.status = "blocked"
            self.state.blockers.append("gate_1_rejected")
        self._save_state()
        self._append_event("research_approved", "Research Agent", str(research_md_path))
        self._create_handoff("intake_to_research")
        self.sync_progress()
        return str(research_md_path), str(system_map_md_path)

    def run_prd(self) -> str:
        """Executa PRD Agent e gera prd.md."""
        from cvg_harness.prd.prd_agent import PRDAgent, save_prd, save_prd_markdown

        research_path = self.artifacts_dir / "research-notes.json"
        if not research_path.exists():
            raise ValueError("research-notes.json required before PRD")

        with open(research_path) as f:
            research = json.load(f)

        with open(self.state.classification_path) as f:
            classification = json.load(f)

        agent = PRDAgent()
        prd = agent.create_prd(self.project, self.feature, research, classification)

        prd_json_path = self.artifacts_dir / "prd.json"
        prd_md_path = self.artifacts_dir / "prd.md"
        save_prd(prd, prd_json_path)
        save_prd_markdown(prd, prd_md_path)

        self.state.prd_path = str(prd_json_path)
        self.state.current_gate = "GATE_2"
        self.state.current_phase = "prd"
        self.state.last_event = "prd_approved"
        # Avaliação formal de GATE_2
        gate_result = self._evaluate_and_save_gate("GATE_2", prd.to_dict(), str(prd_json_path))
        if gate_result.state == "rejected":
            self.state.status = "blocked"
            self.state.blockers.append("gate_2_rejected")
        self._save_state()
        self._append_event("prd_approved", "PRD Agent", str(prd_md_path))
        self._create_handoff("research_to_prd")
        self.sync_progress()
        return str(prd_md_path)

    def build_spec(self) -> tuple[str, str]:
        """Executa Spec Builder e gera spec.md e spec.json com versão sincronizada."""
        from cvg_harness.spec_builder.spec_builder import (
            SpecBuilderAgent, save_spec, save_spec_markdown
        )

        prd_path = self.artifacts_dir / "prd.json"
        research_path = self.artifacts_dir / "research-notes.json"
        if not prd_path.exists() or not research_path.exists():
            raise ValueError("prd.json and research-notes.json required before SPEC")

        with open(prd_path) as f:
            prd = json.load(f)
        with open(research_path) as f:
            research = json.load(f)
        with open(self.state.classification_path) as f:
            classification = json.load(f)

        agent = SpecBuilderAgent()
        spec = agent.build(prd, research, classification)

        spec_json_path = self.artifacts_dir / "spec.json"
        spec_md_path = self.artifacts_dir / "spec.md"

        spec_json = spec.to_dict()
        spec_json["version"] = spec.version
        save_spec(spec, spec_json_path)
        save_spec_markdown(spec, spec_md_path)

        self.state.spec_path = str(spec_json_path)
        self.state.current_gate = "GATE_3"
        self.state.current_phase = "spec"
        self.state.last_event = "spec_created"
        # Avaliação formal de GATE_3
        gate_result = self._evaluate_and_save_gate("GATE_3", spec_json, str(spec_json_path))
        if gate_result.state == "rejected":
            self.state.status = "blocked"
            self.state.blockers.append("gate_3_rejected")
        self._save_state()
        self._append_event("spec_created", "Spec Builder", str(spec_md_path))
        self._create_handoff("prd_to_spec")
        self.sync_progress()
        return str(spec_md_path), str(spec_json_path)

    def plan_sprints(self) -> str:
        """Executa Sprint Planner e gera sprint-plan.json e execution-order.json."""
        from cvg_harness.sprint.sprint_planner import SprintPlanner, save_sprint_plan

        if not self.state.spec_path:
            raise ValueError("spec.json required before sprint planning")

        with open(self.state.spec_path) as f:
            spec = json.load(f)

        planner = SprintPlanner()
        sprint_plan = planner.plan(spec, self.mode)

        sprint_plan_path = self.artifacts_dir / "sprint-plan.json"
        save_sprint_plan(sprint_plan, sprint_plan_path)

        # Persiste execution-order.json explicitamente
        execution_order_path = self.artifacts_dir / "execution-order.json"
        execution_order_data = {
            "sequencia": sprint_plan.execution_order,
            "bloqueios": [],  # seria populado baseado em dependências
            "paralelismo_permitido": False,
            "pre_conds": {},
            "sprint_ids": sprint_plan.execution_order,
        }
        with open(execution_order_path, "w") as f:
            json.dump(execution_order_data, f, indent=2)

        self.state.sprint_plan_path = str(sprint_plan_path)
        self.state.sprint_id = sprint_plan.sprints[0].sprint_id if sprint_plan.sprints else "SPRINT-1"
        self.state.current_gate = "GATE_5"
        self.state.current_phase = "sprint"
        self.state.last_event = "sprint_planned"
        # Avaliação formal de GATE_5
        gate_result = self._evaluate_and_save_gate("GATE_5", sprint_plan.to_dict(), str(sprint_plan_path))
        if gate_result.state == "rejected":
            self.state.status = "blocked"
            self.state.blockers.append("gate_5_rejected")
        self._save_state()
        self._append_event("sprint_planned", "Sprint Planner", str(sprint_plan_path))
        self._append_event("sprint_started", "FlowOrchestrator", str(sprint_plan_path))
        self._create_handoff("spec_to_sprint")
        self.sync_progress()
        return str(sprint_plan_path)

    def evaluate_sprint(self, evidence_files: list[str], round_num: int = 1, evidence_items: Optional[list[dict]] = None) -> dict:
        """Executa Evaluator e valida resultado da sprint."""
        from cvg_harness.evaluator.evaluator import Evaluator, save_evaluation

        if not self.state.spec_path:
            raise ValueError("spec.json required before evaluation")

        with open(self.state.spec_path) as f:
            spec = json.load(f)

        evaluator = Evaluator()
        evaluate_kwargs = {
            "sprint_id": self.state.sprint_id or "SPRINT-1",
            "spec": spec,
            "evidence_files": evidence_files,
            "round_num": round_num,
        }
        if evidence_items is not None and "evidence_items" in inspect.signature(evaluator.evaluate).parameters:
            evaluate_kwargs["evidence_items"] = evidence_items
        report = evaluator.evaluate(**evaluate_kwargs)

        report_path = self.reports_dir / "evaluation-report.json"
        save_evaluation(report, report_path)

        self.state.current_gate = "GATE_7"

        # Avaliação formal de GATE_7
        gate_result = self._evaluate_and_save_gate("GATE_7", report.to_dict(), str(report_path))

        if report.result == "FAILED":
            # Integrar com FallbackPolicy
            fallback = self._handle_evaluator_failure(round_num, report)
            action = fallback.get("action", "unknown")
            self.state.last_event = f"evaluation_failed:{action}"
            self._append_event(
                "evaluation_failed",
                "Evaluator",
                str(report_path),
                metadata={"action": action, "round": round_num},
            )
            self._append_event("sprint_failed", "Evaluator", str(report_path))
        else:
            self.state.last_event = "evaluation_passed"
            self._append_event(
                "evaluation_passed",
                "Evaluator",
                str(report_path),
                metadata={"round": round_num},
            )
            self._append_event("sprint_approved", "Evaluator", str(report_path))
            # Clear any previous blocker
            if "evaluation_failed" in self.state.blockers:
                self.state.blockers.remove("evaluation_failed")

        self._save_state()
        self.sync_progress()
        return report.to_dict()

    def _handle_evaluator_failure(self, round_count: int, report: dict) -> dict:
        """Processa falha do evaluator usando FallbackPolicy."""
        from cvg_harness.fallback.fallback_policy import FallbackPolicy, save_fallback_event

        with open(self.state.spec_path) as f:
            spec = json.load(f)

        policy = FallbackPolicy()
        fallback = policy.evaluate_evaluator_failure(round_count, spec, {})

        # Salva evento de fallback
        fallback_path = self.artifacts_dir / "fallback-events.jsonl"
        save_fallback_event(fallback, fallback_path)

        if fallback.action == "replan":
            # Aciona Replan Coordinator
            replan_decision = self._trigger_replan()
            self._append_event("replan_requested", "FallbackPolicy", str(replan_decision))
            self.state.status = "blocked"
            if "evaluation_failed" not in self.state.blockers:
                self.state.blockers.append("evaluation_failed")
        elif fallback.action == "block":
            self.state.status = "blocked"
            if "evaluation_failed" not in self.state.blockers:
                self.state.blockers.append("evaluation_failed")

        return fallback.to_dict()

    def _trigger_replan(self) -> dict:
        """Aciona ReplanCoordinator."""
        from cvg_harness.replan.replan_coordinator import ReplanCoordinator, save_replan_decision

        coordinator = ReplanCoordinator()
        decision = coordinator.evaluate(
            trigger="evaluator_failures",
            context={"failures": 3},
            current_spec=self.state.spec_path and json.load(open(self.state.spec_path)) or None,
            current_classification=self.state.classification_path and json.load(open(self.state.classification_path)) or None,
        )

        replan_path = self.artifacts_dir / "replan-decision.json"
        save_replan_decision(decision, replan_path)
        self._append_event("replan_requested", "ReplanCoordinator", str(replan_path))
        return decision.to_dict()

    def grant_waiver(self, waiver_data: dict) -> bool:
        """Concede waiver para um bloqueio."""
        from cvg_harness.fallback.fallback_policy import can_grant_waiver

        if can_grant_waiver(waiver_data):
            waiver_path = self.artifacts_dir / "waiver.json"
            with open(waiver_path, "w") as f:
                json.dump(waiver_data, f, indent=2)
            blocker = waiver_data.get("blocker", "unknown")
            if blocker in self.state.blockers:
                self.state.blockers.remove(blocker)
            self._append_event("waiver_granted", "waiver", str(waiver_path))
            self._save_state()
            return True
        return False

    def check_release_readiness(self) -> dict:
        """Executa Release Readiness Engine."""
        from cvg_harness.release.release_readiness import ReleaseReadinessEngine, save_release_readiness

        engine = ReleaseReadinessEngine()

        # Carregar evaluation report
        evaluation_report_path = self.reports_dir / "evaluation-report.json"
        evaluation_report = {}
        if evaluation_report_path.exists():
            with open(evaluation_report_path) as f:
                evaluation_report = json.load(f)

        # Carregar drift report
        drift_report_path = self.reports_dir / "drift-report.json"
        drift_report = {}
        if drift_report_path.exists():
            with open(drift_report_path) as f:
                drift_report = json.load(f)

        # Primeira avaliação: carregar GATE_0-GATE_8 (GATE_9 ainda não existe)
        # Usada para obter a primeira versão do assessment e avaliar GATE_9
        gate_results = []
        for gate_name in ["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5", "GATE_6", "GATE_7", "GATE_8"]:
            gate_file = self.gates_dir / f"gate-{gate_name}.json"
            if gate_file.exists():
                with open(gate_file) as f:
                    gate_results.append(json.load(f))

        preliminary_assessment = engine.assess(
            project=self.project,
            feature=self.feature,
            gate_results=gate_results,
            evaluation_report=evaluation_report,
            drift_report=drift_report,
        )

        assessment_path = self.reports_dir / "release-readiness-report.json"

        # Avaliar e salvar GATE_9 ANTES da avaliação final para que seja consistente
        gate_result = self._evaluate_and_save_gate("GATE_9", preliminary_assessment.to_dict(), str(assessment_path))

        # Segunda avaliação: agora GATE_9 existe em disco — reload completo
        gate_results_final = []
        for gate_name in ["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5", "GATE_6", "GATE_7", "GATE_8", "GATE_9"]:
            gate_file = self.gates_dir / f"gate-{gate_name}.json"
            if gate_file.exists():
                with open(gate_file) as f:
                    gate_results_final.append(json.load(f))

        assessment = engine.assess(
            project=self.project,
            feature=self.feature,
            gate_results=gate_results_final,
            evaluation_report=evaluation_report,
            drift_report=drift_report,
        )

        # Salvar JSON sidecar em reports/ (canonical JSON para consumo interno)
        save_release_readiness(assessment, assessment_path)

        self.state.current_gate = "GATE_9"
        self.state.current_phase = "release"
        self.state.last_event = "release_approved" if assessment.decision == "APPROVED" else "release_rejected"
        if assessment.decision == "APPROVED":
            self.state.status = "completed"
            if "release_rejected" in self.state.blockers:
                self.state.blockers.remove("release_rejected")
        elif assessment.decision == "REJECTED" or gate_result.state == "rejected":
            self.state.status = "blocked"
            if "release_rejected" not in self.state.blockers:
                self.state.blockers.append("release_rejected")
        self._save_state()
        self._append_event(self.state.last_event, "Release Readiness", str(assessment_path))
        self.sync_progress()
        return assessment.to_dict()

    def _create_handoff(self, template_key: str) -> None:
        """Cria e salva handoff na workspace."""
        from cvg_harness.contracts.handoff import HANDOFF_TEMPLATES, save_handoff

        template = HANDOFF_TEMPLATES.get(template_key)
        if template:
            handoff_path = self.artifacts_dir / f"handoff-{template_key}.json"
            save_handoff(template, handoff_path)

    def advance_phase(self, phase: str) -> None:
        """Avança para próxima fase."""
        self.state.current_phase = phase
        self.state.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_state()

    def block(self, reason: str) -> None:
        """Bloqueia o fluxo."""
        self.state.status = "blocked"
        if reason not in self.state.blockers:
            self.state.blockers.append(reason)
        self.state.last_event = f"blocked:{reason}"
        self._save_state()

    def get_state(self) -> FlowState:
        return self.state

    def sync_progress(self) -> str:
        """Sincroniza estado do flow com progress.json para compatibilidade."""
        from cvg_harness.ledger.progress_ledger import ProgressLedger, save_progress

        ledger = ProgressLedger.new(self.project, self.feature, self.mode)
        ledger.current_gate = self.state.current_gate
        ledger.current_sprint = self.state.sprint_id
        ledger.status = self.state.status
        ledger.blockers = self.state.blockers[:]

        # Mapear fase para gate mais próximo
        phase_to_gate = {
            "intake": "GATE_0",
            "classification": "GATE_0",
            "research": "GATE_1",
            "prd": "GATE_2",
            "spec": "GATE_3",
            "lint": "GATE_4",
            "sprint": "GATE_5",
            "execution": "GATE_6",
            "evaluation": "GATE_7",
            "release": "GATE_9",
        }
        for phase, gate in phase_to_gate.items():
            ledger.gates[gate] = "approved" if self.state.current_phase == phase else ledger.gates[gate]
        ledger.gates[self.state.current_gate] = "approved"

        progress_path = self.workspace / "progress.json"
        save_progress(ledger, progress_path)
        return str(progress_path)

    def _save_state(self) -> None:
        path = self.workspace / "flow-state.json"
        with open(path, "w") as f:
            json.dump(self.state.to_dict(), f, indent=2)

    def _append_event(
        self,
        event_type: str,
        actor: str,
        artifact_ref: str = "",
        metadata: Optional[dict] = None,
    ) -> None:
        from cvg_harness.ledger.event_log import Event, save_event
        event = Event.create(
            event_type=event_type,
            actor=actor,
            artifact_ref=artifact_ref,
            metadata=metadata,
        )
        log_path = self.workspace / "event-log.jsonl"
        save_event(event, log_path)

    @classmethod
    def load(cls, workspace: Path) -> "FlowOrchestrator":
        """Carrega estado de workspace existente."""
        state_path = workspace / "flow-state.json"
        with open(state_path) as f:
            data = json.load(f)
        orch = cls(data["project"], data["feature"], data["mode"], workspace, context_workspace=workspace)
        orch.state = FlowState(**data)
        return orch
