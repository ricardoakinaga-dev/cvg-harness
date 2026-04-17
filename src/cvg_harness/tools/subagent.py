from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cvg_harness.drift import DriftDetector
from cvg_harness.evaluator.evaluator import Evaluator, save_evaluation
from cvg_harness.guardian.architecture_guardian import ArchitectureGuardian
from cvg_harness.metrics_agg.metrics_aggregator import MetricsAggregator
from cvg_harness.prd.prd_agent import PRDAgent, save_prd, save_prd_markdown
from cvg_harness.replan.replan_coordinator import ReplanCoordinator
from cvg_harness.release.release_readiness import ReleaseReadinessEngine, save_release_readiness
from cvg_harness.research.research_agent import ResearchAgent
from cvg_harness.research.research_agent import save_research, save_research_markdown, save_system_map, save_system_map_markdown
from cvg_harness.sprint.sprint_planner import SprintPlanner, save_sprint_plan
from cvg_harness.spec_builder.spec_builder import SpecBuilderAgent, save_spec, save_spec_markdown
from cvg_harness.linter.spec_linter import lint_spec, save_lint_report


@dataclass
class SubagentTask:
    task_id: str
    agent_type: str
    status: str
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    error: str | None = None
    context_snapshot: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    finished_at: str = ""


class SubagentTool:
    """Toolset mínimo de subagentes internos (orquestrável e observável)."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self._tasks: dict[str, SubagentTask] = {}

    def spawn(self, agent_type: str, input: str | dict[str, Any], context: dict[str, Any], max_tokens: int = 1200) -> str:
        normalized_agent = (agent_type or "").strip().lower()
        payload = self._normalize_input(input)
        task_id = str(uuid.uuid4())
        task = SubagentTask(
            task_id=task_id,
            agent_type=normalized_agent,
            status="running",
            input=payload,
            context_snapshot=self._safe_context(context),
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self._tasks[task_id] = task
        try:
            output = self._execute(normalized_agent, payload, context, max_tokens=max_tokens)
            task.output = output
            task.status = "done"
        except Exception as exc:  # pragma: no cover - defensive path
            task.status = "failed"
            task.error = str(exc)
            task.output = {"status": "failed", "reason": str(exc)}
        task.finished_at = datetime.now(timezone.utc).isoformat()
        return task_id

    def await_result(self, task_id: str) -> dict[str, Any]:
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"task não encontrado: {task_id}")
        if task.status == "running":
            task.status = "done"
            task.finished_at = datetime.now(timezone.utc).isoformat()
            task.output = {"status": "done", "result": task.output or {}}
        return task.output or {"status": task.status}

    def merge_result(self, task_id: str) -> dict[str, Any]:
        result = self.await_result(task_id)
        return {
            "task_id": task_id,
            "status": (self._tasks[task_id].status),
            "agent_type": self._tasks[task_id].agent_type,
            "result": result,
        }

    def _execute(
        self,
        agent_type: str,
        input: dict[str, Any],
        context: dict[str, Any],
        max_tokens: int,
    ) -> dict[str, Any]:
        method = self._METHODS.get(agent_type)
        if not method:
            return {
                "status": "skipped",
                "agent_type": agent_type,
                "reason": "subagente indisponível",
            }
        return method(input, context, max_tokens=max_tokens)

    def _normalize_input(self, value: str | dict[str, Any]) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if value is None:
            return {}
        return {"text": str(value)}

    def _safe_context(self, context: dict[str, Any]) -> dict[str, Any]:
        run_workspace = context.get("run_workspace")
        return {
            "workspace": str(context.get("workspace") or ""),
            "run_workspace": str(run_workspace) if run_workspace else "",
            "mode": str(context.get("mode", "")),
        }

    def _run_research(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        artifacts = run_workspace / "artifacts"
        demand = input.get("intent") or input.get("text", "")
        project = str(context.get("project") or self.workspace_root.name)
        classification = self._load_json(run_workspace / "artifacts" / "classification.json")
        if not classification:
            classification = {
                "project": project,
                "feature": demand,
                "mode": "FAST",
                "rationale": input.get("rationale", ""),
                "total_score": 0,
                "dimensions": {},
            }
        research, system_map = ResearchAgent().investigate(project, demand, classification, workspace=self.workspace_root)
        research_path = artifacts / "research-notes.json"
        system_map_path = artifacts / "system-map.json"
        save_research(research, research_path)
        save_system_map(system_map, system_map_path)
        save_research_markdown(research, artifacts / "research-notes.md")
        save_system_map_markdown(system_map, artifacts / "system-map.md")
        return {
            "status": "done",
            "artifacts": [
                str(research_path),
                str(system_map_path),
            ],
            "modules": research.modulos,
        }

    def _run_prd(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        artifacts = run_workspace / "artifacts"
        feature = input.get("intent") or input.get("text", "")
        classification = self._load_json(artifacts / "classification.json")
        research_notes = self._load_json(artifacts / "research-notes.json")
        if not classification or not research_notes:
            return {
                "status": "failed",
                "reason": "research-notes/classification ausentes para gerar PRD",
            }
        prd = PRDAgent().create_prd(self.workspace_root.name, feature, research_notes, classification)
        prd_json = artifacts / "prd.json"
        prd_md = artifacts / "prd.md"
        save_prd(prd, prd_json)
        save_prd_markdown(prd, prd_md)
        return {
            "status": "done",
            "artifacts": [str(prd_json), str(prd_md)],
            "feature": feature,
        }

    def _run_spec_builder(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        artifacts = run_workspace / "artifacts"
        prd = self._load_json(artifacts / "prd.json")
        research = self._load_json(artifacts / "research-notes.json")
        classification = self._load_json(artifacts / "classification.json")
        if not prd or not research or not classification:
            return {
                "status": "failed",
                "reason": "dependências insuficientes para SPEC",
            }
        spec = SpecBuilderAgent().build(prd, research, classification)
        spec_json = artifacts / "spec.json"
        spec_md = artifacts / "spec.md"
        save_spec(spec, spec_json)
        save_spec_markdown(spec, spec_md)
        return {
            "status": "done",
            "artifacts": [str(spec_json), str(spec_md)],
            "modulos": spec.modulos,
        }

    def _run_spec_linter(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        artifacts = run_workspace / "artifacts"
        spec = self._load_json(artifacts / "spec.json")
        if not spec:
            return {"status": "failed", "reason": "spec.json ausente"}
        classification = self._load_json(artifacts / "classification.json")
        mode = classification.get("mode", "FAST") if isinstance(classification, dict) else "FAST"
        report = lint_spec(spec, mode=mode)
        report_path = run_workspace / "reports" / "spec-lint-report.json"
        save_lint_report(report, report_path)
        return {
            "status": "done",
            "result": report.result,
            "report": str(report_path),
            "score": report.score,
        }

    def _run_sprint_planner(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        artifacts = run_workspace / "artifacts"
        spec = self._load_json(artifacts / "spec.json")
        classification = self._load_json(artifacts / "classification.json")
        if not spec:
            return {"status": "failed", "reason": "spec.json ausente"}
        mode = classification.get("mode", "FAST") if isinstance(classification, dict) else "FAST"
        planner = SprintPlanner()
        sprint_plan = planner.plan(spec, mode=mode)
        sprint_path = artifacts / "sprint-plan.json"
        execution_path = artifacts / "execution-order.json"
        save_sprint_plan(sprint_plan, sprint_path)
        execution_path.write_text(json.dumps({"sequencia": sprint_plan.execution_order}, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "status": "done",
            "sprints": len(sprint_plan.sprints),
            "artifacts": [str(sprint_path), str(execution_path)],
        }

    def _run_evaluator(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        reports_dir = run_workspace / "reports"
        spec = self._load_json(run_workspace / "artifacts" / "spec.json")
        if not spec:
            return {"status": "failed", "reason": "spec.json ausente"}
        evaluator = Evaluator()
        evidence_items = input.get("evidence_items") or []
        evidence_files = input.get("evidence_files") or []
        report = evaluator.evaluate(
            sprint_id=input.get("sprint_id", "SPRINT-1"),
            spec=spec,
            evidence_files=evidence_files,
            round_num=int(input.get("round", 1)),
            evidence_items=evidence_items,
        )
        report_path = reports_dir / "evaluation-report.json"
        save_evaluation(report, report_path)
        return {
            "status": "done",
            "result": report.result,
            "report": str(report_path),
            "next_action": report.next_action,
        }

    def _run_architecture_guardian(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        spec = self._load_json(run_workspace / "artifacts" / "spec.json")
        changed_files = input.get("changed_files") or []
        if not spec:
            return {"status": "failed", "reason": "spec.json ausente"}
        guardian = ArchitectureGuardian(
            authorized_areas=spec.get("areas_autorizadas", []),
            prohibited_areas=spec.get("areas_proibidas", []),
            boundaries=spec.get("boundaries", []),
        )
        report = guardian.check(changed_files=changed_files, new_dependencies=input.get("new_dependencies") or [])
        path = run_workspace / "reports" / "architecture-guard-report.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "done", "result": report.result, "violations": len(report.violations), "report": str(path)}

    def _run_drift_detector(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        reports = run_workspace / "reports"
        intake = self._load_json(run_workspace / "artifacts" / "classification.json")
        prd = self._load_json(run_workspace / "artifacts" / "prd.json")
        spec = self._load_json(run_workspace / "artifacts" / "spec.json")
        sprint_plan = self._load_json(run_workspace / "artifacts" / "sprint-plan.json")
        evaluation = self._load_json(reports / "evaluation-report.json")
        release_readiness = self._load_json(reports / "release-readiness-report.json")
        detector = DriftDetector(sprint_id=input.get("sprint_id", "SPRINT-1"))
        report = detector.detect(
            intake=intake,
            prd=prd,
            spec=spec,
            sprint_plan=sprint_plan,
            evaluation=evaluation,
            release_readiness=release_readiness,
        )
        path = reports / "drift-report.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "done", "result": report.result, "report": str(path), "findings": len(report.findings)}

    def _run_release_readiness(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        reports = run_workspace / "reports"
        gate_inputs = self._collect_gate_inputs(reports)
        evaluation = self._load_json(reports / "evaluation-report.json")
        drift = self._load_json(reports / "drift-report.json")
        engine = ReleaseReadinessEngine()
        assessment = engine.assess(
            project=context.get("project", self.workspace_root.name),
            feature=input.get("intent", ""),
            gate_results=gate_inputs,
            evaluation_report=evaluation or {},
            drift_report=drift or {},
        )
        path = reports / "release-readiness-report.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        save_release_readiness(assessment, path)
        return {"status": "done", "decision": assessment.decision, "report": str(path)}

    def _run_replan_coordinator(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        reason = str(input.get("reason") or "trigger")
        coordinator = ReplanCoordinator()
        decision = coordinator.evaluate(
            trigger="replan",  # fallback compat
            context={"reason": reason, "mode": context.get("mode", "UNKNOWN")},
        )
        decision_path = self._run_workspace(context) / "artifacts" / "replan-decision.json"
        decision_path.parent.mkdir(parents=True, exist_ok=True)
        decision_path.write_text(json.dumps(decision.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "done", "action": decision.action, "reason": decision.reason, "report": str(decision_path)}

    def _run_metrics_aggregator(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del max_tokens
        run_workspace = self._run_workspace(context)
        reports = run_workspace / "reports"
        progress = run_workspace / "progress.json"
        aggregator = MetricsAggregator()
        metrics = aggregator.aggregate(
            project=context.get("project", self.workspace_root.name),
            feature=input.get("intent", ""),
            mode=str(context.get("mode", "FAST")),
            event_log_path=run_workspace / "ledger-eventlog.jsonl",
            progress_path=progress if progress.exists() else None,
        )
        path = run_workspace / "reports" / "delivery-metrics.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(metrics.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return {"status": "done", "report": str(path), "sprints_count": metrics.sprints_count}

    def _run_implementation(self, input: dict[str, Any], context: dict[str, Any], max_tokens: int) -> dict[str, Any]:
        del input, context, max_tokens
        return {
            "status": "simulated",
            "message": "implementação delegada ao operador de execução",
        }

    @property
    def _METHODS(self) -> dict[str, Any]:
        return {
            "research": self._run_research,
            "prd": self._run_prd,
            "spec_builder": self._run_spec_builder,
            "spec_linter": self._run_spec_linter,
            "sprint_planner": self._run_sprint_planner,
            "evaluator": self._run_evaluator,
            "architecture_guardian": self._run_architecture_guardian,
            "drift_detector": self._run_drift_detector,
            "release_readiness": self._run_release_readiness,
            "replan_coordinator": self._run_replan_coordinator,
            "metrics_aggregator": self._run_metrics_aggregator,
            "implement": self._run_implementation,
        }

    def _run_workspace(self, context: dict[str, Any]) -> Path:
        run_ws = context.get("run_workspace")
        if run_ws:
            path = Path(run_ws)
            if path.exists():
                return path
        fallback = self.workspace_root / ".harness"
        return fallback

    def _load_json(self, path: Path) -> dict[str, Any] | list[Any] | None:
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, (dict, list)):
            return data
        return None

    def _collect_gate_inputs(self, reports_dir: Path) -> list[dict[str, Any]]:
        gates_dir = reports_dir / "gates"
        if not gates_dir.exists():
            return []
        result = []
        for gate_file in sorted(gates_dir.glob("gate-*.json")):
            result.append(self._load_json(gate_file) or {})
        return result
