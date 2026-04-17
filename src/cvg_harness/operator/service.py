from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.request import urlopen

from cvg_harness.auto_runtime.external_executor import (
    ExternalExecutorBridge,
    ExecutionDispatchRequest,
    create_default_executor_registry,
    load_executor_registry,
    save_executor_registry,
)
from cvg_harness.auto_runtime.runtime_automation import (
    HookEvent,
    RuntimeExecutor,
    create_automation,
    create_default_automation,
    get_context_hints,
    get_profile_events,
    get_required_context,
    get_runtime_profile,
    list_runtime_profiles,
    resolve_runtime_context,
)
from cvg_harness.flow import FlowOrchestrator
from cvg_harness.ledger.event_log import Event, load_events, save_event
from cvg_harness.ledger.progress_ledger import load_progress
from cvg_harness.metrics_agg.metrics_aggregator import MetricsAggregator
from cvg_harness.replan.replan_coordinator import ReplanCoordinator, ReplanTrigger, save_replan_decision


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_CAPABILITY_POLICIES = {
    "ci": {
        "preferred_providers": ["github-actions", "gitlab-ci", "azure-pipelines", "generic-ci"],
        "preferred_adapters": [],
        "disabled_adapters": [],
        "prefer_manual": False,
    },
    "review": {
        "preferred_providers": ["human-review"],
        "preferred_adapters": [],
        "disabled_adapters": [],
        "prefer_manual": True,
    },
    "evidence": {
        "preferred_providers": ["github-actions", "gitlab-ci", "azure-pipelines", "human-review"],
        "preferred_adapters": [],
        "disabled_adapters": [],
        "prefer_manual": False,
    },
}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "run"


def infer_dimensions_from_demand(demand: str) -> tuple[dict[str, int], str]:
    text = demand.lower()
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

    def bump(key: str, value: int) -> None:
        dims[key] = max(dims[key], value)

    if any(word in text for word in ["auth", "oauth", "permission", "permiss", "setor", "role", "acl"]):
        bump("impacto_arquitetural", 2)
        bump("criticidade_de_negocio", 2)
        bump("sensibilidade_de_dados", 2)
    if any(word in text for word in ["payment", "billing", "finance", "fatur", "invoice"]):
        bump("criticidade_de_negocio", 3)
        bump("risco_de_regressao", 2)
        bump("sensibilidade_de_dados", 2)
    if any(word in text for word in ["integration", "webhook", "extern", "api externa", "terceiro"]):
        bump("dependencia_externa", 2)
        bump("impacto_arquitetural", 2)
    if any(word in text for word in ["refactor", "migra", "legacy", "deprecat", "core"]):
        bump("impacto_arquitetural", 2)
        bump("reversibilidade", 2)
        bump("risco_de_regressao", 2)
    if any(word in text for word in ["module", "módulo", "workflow", "fluxo", "engine"]):
        bump("modulos_afetados", 2)
        bump("complexidade_de_validacao", 2)

    rationale = (
        "Dimensões inferidas heuristicamente a partir do texto da demanda; "
        "o operador pode revisar via status/inspect e forçar ENTERPRISE quando necessário."
    )
    return dims, rationale


@dataclass
class OperatorRunRecord:
    run_id: str
    project: str
    demand: str
    workspace_root: str
    run_workspace: str
    mode: str
    operator_status: str
    next_action: str
    pending_human_action: str = ""
    current_phase: str = "intake"
    current_gate: str = "GATE_0"
    current_sprint: str = ""
    summary: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)


class OperatorService:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.root = self.base_dir / ".cvg-harness"
        self.runs_dir = self.root / "runs"
        self.logs_dir = self.root / "logs"
        self.ledgers_dir = self.root / "ledgers"
        self.reports_dir = self.root / "reports"
        self.artifacts_dir = self.root / "artifacts"
        self.current_run_file = self.root / "current-run.txt"
        self.index_file = self.root / "run-index.json"
        self.executors_registry_file = self.root / "executors.json"
        self.adapter_policy_file = self.root / "adapter-policy.json"
        self._ensure_root()

    def _ensure_root(self) -> None:
        for path in [self.root, self.runs_dir, self.logs_dir, self.ledgers_dir, self.reports_dir, self.artifacts_dir]:
            path.mkdir(parents=True, exist_ok=True)
        if not self.index_file.exists():
            self.index_file.write_text(json.dumps({"runs": []}, indent=2))
        if not self.executors_registry_file.exists():
            save_executor_registry(create_default_executor_registry(), self.executors_registry_file)

    def _run_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def _run_record_path(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "run.json"

    def _event_log_path(self, run_workspace: Path) -> Path:
        return run_workspace / "event-log.jsonl"

    def _load_json_if_exists(self, path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def _append_operator_event(self, run_workspace: Path, event_type: str, metadata: Optional[dict] = None) -> None:
        save_event(Event.create(event_type, "Operator CLI", str(run_workspace), metadata or {}), self._event_log_path(run_workspace))

    def _save_run_record(self, record: OperatorRunRecord) -> None:
        record.updated_at = _now()
        path = self._run_record_path(record.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record.to_dict(), indent=2))
        index = json.loads(self.index_file.read_text())
        runs = [entry for entry in index.get("runs", []) if entry.get("run_id") != record.run_id]
        runs.append({
            "run_id": record.run_id,
            "project": record.project,
            "demand": record.demand,
            "run_workspace": record.run_workspace,
            "operator_status": record.operator_status,
            "updated_at": record.updated_at,
        })
        index["runs"] = runs
        self.index_file.write_text(json.dumps(index, indent=2))
        self.current_run_file.write_text(record.run_id)

    def _load_run_record(self, run_id: str) -> OperatorRunRecord:
        return OperatorRunRecord(**json.loads(self._run_record_path(run_id).read_text()))

    def _normalize_evidence_item(self, item: Any) -> dict:
        if isinstance(item, str):
            return {
                "kind": "note",
                "summary": item,
                "source": "operator_text",
                "ref": "",
                "module": "",
                "metadata": {},
            }
        if not isinstance(item, dict):
            raise ValueError("Evidência estruturada deve ser string ou objeto JSON")
        summary = item.get("summary") or item.get("text") or item.get("description") or item.get("name") or item.get("ref")
        if not summary:
            raise ValueError("Evidência estruturada precisa de summary/text/description/name/ref")
        return {
            "kind": item.get("kind", "note"),
            "summary": str(summary),
            "source": item.get("source", "operator_structured"),
            "ref": item.get("ref", ""),
            "module": item.get("module", ""),
            "metadata": item.get("metadata", {}),
        }

    def _load_evidence_file_items(self, evidence_file: Optional[str]) -> list[Any]:
        if not evidence_file:
            return []
        payload = json.loads(Path(evidence_file).read_text())
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            if isinstance(payload.get("items"), list):
                return payload["items"]
            if isinstance(payload.get("evidence"), list):
                return payload["evidence"]
            return [payload]
        raise ValueError("Arquivo de evidência deve conter objeto ou lista JSON")

    def _normalize_evidence_inputs(self, evidence=None, evidence_json=None, evidence_file=None) -> list[dict]:
        items: list[dict] = []
        for raw in evidence or []:
            items.append(self._normalize_evidence_item(raw))
        for raw in evidence_json or []:
            items.append(self._normalize_evidence_item(json.loads(raw)))
        for raw in self._load_evidence_file_items(evidence_file):
            items.append(self._normalize_evidence_item(raw))
        return items

    def _normalize_ci_result_input(
        self,
        ci_result: Optional[dict] = None,
        ci_result_json: Optional[str] = None,
        ci_result_file: Optional[str] = None,
        ci_result_url: Optional[str] = None,
    ) -> dict:
        payload: Optional[dict]
        if ci_result is not None:
            payload = dict(ci_result)
        elif ci_result_json:
            payload = json.loads(ci_result_json)
        elif ci_result_file:
            payload = json.loads(Path(ci_result_file).read_text())
        elif ci_result_url:
            with urlopen(ci_result_url) as response:
                payload = json.loads(response.read().decode("utf-8"))
        else:
            payload = None

        if payload is None:
            return {}
        if not isinstance(payload, dict):
            raise ValueError("CI result deve ser um objeto JSON")

        evidence_refs = payload.get("evidence_refs") or []
        if isinstance(evidence_refs, str):
            evidence_refs = [evidence_refs]
        if not isinstance(evidence_refs, list):
            raise ValueError("CI result precisa de evidence_refs como lista ou string")

        results = payload.get("results") or []
        if not isinstance(results, list):
            results = [results]

        return {
            "ci_ref": str(payload.get("ci_ref") or payload.get("ci_url") or payload.get("ci_run_id") or payload.get("ci_id") or "ci-result"),
            "status": str(payload.get("status") or payload.get("ci_status") or payload.get("result") or "unknown"),
            "evidence_refs": [str(ref) for ref in evidence_refs if str(ref)],
            "results": results,
            "source": payload.get("source", "external_ci"),
            "metadata": payload.get("metadata", {}),
        }

    def _evidence_strings_for_evaluator(self, items: list[dict]) -> list[str]:
        normalized = []
        for item in items:
            parts = [item.get("summary", "")]
            if item.get("ref"):
                parts.append(str(item["ref"]))
            if item.get("module"):
                parts.append(f"modulo {item['module']}")
            normalized.append(" | ".join(part for part in parts if part))
        return normalized

    def _save_execution_context(self, record: OperatorRunRecord, changed_files: list[str], evidence_items: list[dict], round_num: int) -> tuple[Path, Path]:
        run_workspace = Path(record.run_workspace)
        artifacts_dir = run_workspace / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        execution_payload = {
            "run_id": record.run_id,
            "project": record.project,
            "demand": record.demand,
            "sprint_id": record.current_sprint,
            "round": round_num,
            "changed_files": changed_files,
            "evidence_items": evidence_items,
            "updated_at": _now(),
        }
        execution_path = artifacts_dir / "execution-input.json"
        execution_path.write_text(json.dumps(execution_payload, indent=2, ensure_ascii=False))

        evidence_payload = {
            "run_id": record.run_id,
            "sprint_id": record.current_sprint,
            "round": round_num,
            "items": evidence_items,
            "changed_files": changed_files,
            "normalized_evaluator_inputs": self._evidence_strings_for_evaluator(evidence_items),
            "updated_at": _now(),
        }
        evidence_path = artifacts_dir / "evidence-manifest.json"
        evidence_path.write_text(json.dumps(evidence_payload, indent=2, ensure_ascii=False))
        return execution_path, evidence_path

    def _load_executor_registry(self):
        default_registry = create_default_executor_registry()
        if not self.executors_registry_file.exists():
            save_executor_registry(default_registry, self.executors_registry_file)
            return default_registry
        registry = load_executor_registry(self.executors_registry_file)
        updated = False
        for adapter in default_registry.list():
            if adapter.name not in registry.adapters:
                registry.register(adapter)
                updated = True
        if updated:
            save_executor_registry(registry, self.executors_registry_file)
        return registry

    def _load_capability_policies(self) -> tuple[dict[str, dict], str]:
        policies = json.loads(json.dumps(DEFAULT_CAPABILITY_POLICIES))
        source = "default"
        if not self.adapter_policy_file.exists():
            return policies, source

        payload = json.loads(self.adapter_policy_file.read_text())
        capabilities = payload.get("capabilities", payload)
        if not isinstance(capabilities, dict):
            raise ValueError("adapter-policy.json deve conter objeto JSON em capabilities")

        for capability, policy in capabilities.items():
            if not isinstance(policy, dict):
                continue
            target = policies.setdefault(
                capability,
                {
                    "preferred_providers": [],
                    "preferred_adapters": [],
                    "disabled_adapters": [],
                    "prefer_manual": False,
                },
            )
            if "prefer_manual" in policy:
                target["prefer_manual"] = bool(policy["prefer_manual"])
            for field_name in ("preferred_providers", "preferred_adapters", "disabled_adapters"):
                if field_name not in policy:
                    continue
                value = policy[field_name]
                if not isinstance(value, list):
                    raise ValueError(f"adapter-policy.json: {capability}.{field_name} deve ser lista")
                target[field_name] = [str(item) for item in value if str(item)]
        return policies, "default+project"

    def _resolve_capability_policy(self, capability: Optional[str]) -> tuple[dict, str]:
        policies, source = self._load_capability_policies()
        if not capability:
            return {}, source
        return dict(policies.get(capability, {})), source

    def _current_sprint_payload(self, run_workspace: Path, sprint_id: str) -> Optional[dict]:
        sprint_plan = self._load_json_if_exists(run_workspace / "artifacts" / "sprint-plan.json") or {}
        return next((s for s in sprint_plan.get("sprints", []) if s.get("sprint_id") == sprint_id), None)

    def _merge_missing_context(self, target: dict, source: Optional[dict]) -> None:
        if not source:
            return
        for key, value in source.items():
            if key not in target and value not in (None, "", [], {}):
                target[key] = value

    def _resolve_dispatch_context(self, run_workspace: Path, context: Optional[dict]) -> tuple[dict, list[str]]:
        resolved = dict(context or {})
        sources: list[str] = []

        runtime_hooks = self._load_json_if_exists(run_workspace / "artifacts" / "runtime-hooks.json") or {}
        if runtime_hooks:
            self._merge_missing_context(resolved, runtime_hooks.get("resolved_context") or runtime_hooks.get("context") or {})
            if runtime_hooks.get("provider") and "runtime_provider" not in resolved:
                resolved["runtime_provider"] = runtime_hooks["provider"]
            sources.append("runtime_hooks")

        ci_result = self._load_json_if_exists(run_workspace / "artifacts" / "ci-result.json") or {}
        if ci_result:
            self._merge_missing_context(resolved, ci_result.get("context") or {})
            ci_ref = ci_result.get("ci_ref")
            status = ci_result.get("status")
            provider = ci_result.get("provider")
            if ci_ref and "ci_ref" not in resolved:
                resolved["ci_ref"] = ci_ref
            if status and "ci_status" not in resolved:
                resolved["ci_status"] = status
            if provider and "ci_provider" not in resolved:
                resolved["ci_provider"] = provider
            sources.append("ci_result")

        if context:
            sources.append("operator_input")

        deduped_sources = []
        for source in sources:
            if source not in deduped_sources:
                deduped_sources.append(source)
        return resolved, deduped_sources

    def _resolve_dispatch_requirements(self, adapter, context_payload: dict) -> dict:
        hints = list(adapter.context_hints)
        required = list(adapter.required_context)
        available_keys = sorted(context_payload.keys())
        missing_hints = []
        if hints and not any(hint in context_payload for hint in hints):
            missing_hints = hints
        missing_required = [key for key in required if key not in context_payload]
        return {
            "provider": adapter.provider,
            "context_hints": hints,
            "required_context": required,
            "missing_context_hints": missing_hints,
            "missing_required_context": missing_required,
            "available_context_keys": available_keys,
            "example_contexts": list(adapter.example_contexts),
            "command_examples": list(adapter.command_examples),
        }

    def _runtime_dispatch_context(self, run_workspace: Path) -> dict:
        runtime_hooks = self._load_json_if_exists(run_workspace / "artifacts" / "runtime-hooks.json") or {}
        if not runtime_hooks:
            return {}
        return {
            "runtime_profile": runtime_hooks.get("profile", "default"),
            "runtime_provider": runtime_hooks.get("provider", ""),
            "runtime_event": runtime_hooks.get("event", ""),
        }

    def _adapter_selection_reason(self, adapter, capability: Optional[str], dispatch_context: dict, requirements: dict) -> list[str]:
        reasons: list[str] = []
        policy, _ = self._resolve_capability_policy(capability)
        if capability and capability in adapter.capabilities:
            reasons.append(f"capability:{capability}")
        runtime_provider = dispatch_context.get("runtime_provider", "")
        ci_provider = dispatch_context.get("ci_provider", "")
        if adapter.provider and adapter.provider in {runtime_provider, ci_provider}:
            reasons.append(f"provider:{adapter.provider}")
        preferred_adapters = set(policy.get("preferred_adapters", []))
        if adapter.name in preferred_adapters:
            reasons.append(f"policy_adapter:{adapter.name}")
        if policy.get("prefer_manual") and adapter.transport == "manual":
            reasons.append("policy:prefer_manual")
        preferred_providers = set(policy.get("preferred_providers", []))
        if adapter.provider and adapter.provider in preferred_providers:
            reasons.append(f"policy_provider:{adapter.provider}")
        disabled_adapters = set(policy.get("disabled_adapters", []))
        if adapter.name in disabled_adapters:
            reasons.append(f"policy_disabled:{adapter.name}")
        if not requirements.get("missing_required_context"):
            reasons.append("required_context_satisfied")
        return reasons

    def _score_adapter(self, adapter, capability: Optional[str], dispatch_context: dict, requirements: dict) -> int:
        score = 0
        policy, _ = self._resolve_capability_policy(capability)
        if capability:
            if capability not in adapter.capabilities:
                return -1
            score += 10
        disabled_adapters = set(policy.get("disabled_adapters", []))
        if adapter.name in disabled_adapters:
            return -1
        runtime_provider = dispatch_context.get("runtime_provider", "")
        ci_provider = dispatch_context.get("ci_provider", "")
        if adapter.provider and adapter.provider in {runtime_provider, ci_provider}:
            score += 5
        preferred_adapters = set(policy.get("preferred_adapters", []))
        if adapter.name in preferred_adapters:
            score += 7
        if policy.get("prefer_manual") and adapter.transport == "manual":
            score += 8
        preferred_providers = set(policy.get("preferred_providers", []))
        if adapter.provider and adapter.provider in preferred_providers:
            score += 2
        if not requirements.get("missing_required_context"):
            score += 3
        if adapter.transport == "cli":
            score += 1
        return score

    def _rank_adapters(self, run_workspace: Path, capability: Optional[str] = None, context: Optional[dict] = None) -> list[dict]:
        registry = self._load_executor_registry()
        resolved_context, context_sources = self._resolve_dispatch_context(run_workspace, context=context)
        dispatch_context = self._runtime_dispatch_context(run_workspace)
        active_policy, policy_source = self._resolve_capability_policy(capability)
        ranked = []
        for adapter in registry.list():
            requirements = self._resolve_dispatch_requirements(adapter, resolved_context)
            score = self._score_adapter(adapter, capability, dispatch_context, requirements)
            if capability and score < 0:
                continue
            payload = adapter.to_dict()
            payload.update({
                "suitability_score": score,
                "selection_reason": self._adapter_selection_reason(adapter, capability, dispatch_context, requirements),
                "missing_required_context": requirements["missing_required_context"],
                "available_context_keys": requirements["available_context_keys"],
                "context_sources": context_sources,
                "policy_source": policy_source,
                "active_policy": active_policy,
            })
            ranked.append(payload)
        ranked.sort(key=lambda item: (-item.get("suitability_score", 0), item.get("name", "")))
        return ranked

    def _select_adapter(self, run_workspace: Path, capability: str, context: Optional[dict] = None):
        ranked = self._rank_adapters(run_workspace, capability=capability, context=context)
        if not ranked:
            raise ValueError(f"Nenhum adapter encontrado para capability {capability}")
        return ranked[0], ranked

    def _prime_external_dispatch_plan(self, record: OperatorRunRecord, run_workspace: Path) -> dict:
        sprint_payload = self._current_sprint_payload(run_workspace, record.current_sprint) or {}
        evidence_targets = []
        for criterion in sprint_payload.get("criterios_aceite", []) or sprint_payload.get("criteria", []) or []:
            if isinstance(criterion, str):
                evidence_targets.append(criterion)
            elif isinstance(criterion, dict) and criterion.get("descricao"):
                evidence_targets.append(criterion["descricao"])

        bridge = ExternalExecutorBridge(self._load_executor_registry())
        adapter = bridge.registry.get("manual-review")
        resolved_context, context_sources = self._resolve_dispatch_context(run_workspace, context=None)
        dispatch_context = self._runtime_dispatch_context(run_workspace)
        requirements = self._resolve_dispatch_requirements(adapter, resolved_context)
        request = ExecutionDispatchRequest(
            run_id=record.run_id,
            sprint_id=record.current_sprint or "SPRINT-1",
            demand=record.demand,
            objective=sprint_payload.get("objetivo") or sprint_payload.get("goal") or record.demand,
            workspace=str(self.base_dir),
            changed_files=[],
            evidence_targets=evidence_targets,
            context=resolved_context,
            context_sources=context_sources,
            metadata={
                "mode": record.mode,
                "primed": True,
                **dispatch_context,
            },
        )
        result = bridge.plan("manual-review", request)
        plan_path = run_workspace / "artifacts" / "external-dispatch-plan.json"
        combined_metadata = {**request.metadata, **result.metadata}
        plan_payload = {
            **request.to_dict(),
            **result.to_dict(),
            **requirements,
            "metadata": combined_metadata,
            "request_metadata": request.metadata,
            "result_metadata": result.metadata,
            "runtime_profile": dispatch_context.get("runtime_profile", ""),
            "runtime_provider": dispatch_context.get("runtime_provider", ""),
            "executor": "manual-review",
            "auto_execute": False,
        }
        plan_path.write_text(json.dumps(plan_payload, indent=2, ensure_ascii=False))
        self._append_operator_event(run_workspace, "external_execution_requested", {
            "executor": result.adapter,
            "status": result.status,
            "artifact": str(plan_path),
            "runtime_profile": dispatch_context.get("runtime_profile", ""),
            "runtime_provider": dispatch_context.get("runtime_provider", ""),
        })
        self._append_operator_event(run_workspace, "external_executor_planned", {
            "executor": result.adapter,
            "status": result.status,
            "artifact": str(plan_path),
            "runtime_profile": dispatch_context.get("runtime_profile", ""),
            "runtime_provider": dispatch_context.get("runtime_provider", ""),
        })
        return {"artifact": str(plan_path), "plan": plan_payload}

    def _build_timeline(self, run_workspace: Path) -> list[dict]:
        interesting = {
            "run_started",
            "run_ready_for_execution",
            "operator_approved",
            "operator_paused",
            "operator_resumed",
            "execution_inputs_registered",
            "evidence_registered",
            "gate_approved",
            "gate_rejected",
            "gate_waived",
            "architecture_guard_failed",
            "architecture_guard_passed",
            "evaluation_failed",
            "evaluation_passed",
            "drift_detected",
            "drift_clean",
            "release_approved",
            "release_rejected",
            "operator_replanned",
            "external_executor_planned",
            "external_executor_dispatched",
            "external_execution_failed",
            "external_evidence_registered",
            "ci_result_registered",
            "runtime_hooks_executed",
        }
        timeline = []
        for event in load_events(self._event_log_path(run_workspace)):
            if event.event_type not in interesting:
                continue
            timeline.append({
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "actor": event.actor,
                "artifact_ref": event.artifact_ref,
                "metadata": event.metadata,
            })
        return timeline

    def _build_causal_summary(self, record: OperatorRunRecord, run_workspace: Path, sprint: Optional[dict]) -> dict:
        progress_path = run_workspace / "progress.json"
        blockers = load_progress(progress_path).blockers if progress_path.exists() else []
        evaluation = self._load_json_if_exists(run_workspace / "reports" / "evaluation-report.json") or {}
        guard = self._load_json_if_exists(run_workspace / "reports" / "architecture-guard-report.json") or {}
        drift = self._load_json_if_exists(run_workspace / "reports" / "drift-report.json") or {}
        release = self._load_json_if_exists(run_workspace / "reports" / "release-readiness-report.json") or {}
        evidence = self._load_json_if_exists(run_workspace / "artifacts" / "evidence-manifest.json") or {}
        execution_input = self._load_json_if_exists(run_workspace / "artifacts" / "execution-input.json") or {}
        dispatch_plan = self._load_json_if_exists(run_workspace / "artifacts" / "external-dispatch-plan.json") or {}
        dispatch_result = self._load_json_if_exists(run_workspace / "reports" / "external-dispatch-result.json") or {}
        runtime_hooks = self._load_json_if_exists(run_workspace / "artifacts" / "runtime-hooks.json") or {}
        external_evidence = self._load_json_if_exists(run_workspace / "artifacts" / "external-evidence-manifest.json") or {}
        ci_result = self._load_json_if_exists(run_workspace / "artifacts" / "ci-result.json") or {}
        runtime_profile = {}
        if runtime_hooks:
            try:
                runtime_profile = get_runtime_profile(runtime_hooks.get("profile", "default"))
            except ValueError:
                runtime_profile = {}

        evidence_items = evidence.get("items", [])
        kinds = Counter(item.get("kind", "unknown") for item in evidence_items)
        refs = [item.get("ref") for item in evidence_items if item.get("ref")]
        criteria = []
        if sprint:
            criteria = sprint.get("criterios_aceite") or sprint.get("acceptance_criteria") or sprint.get("criteria") or []

        return {
            "sprint_id": record.current_sprint,
            "objective": (sprint or {}).get("objetivo") or (sprint or {}).get("goal") or "",
            "acceptance_criteria": criteria,
            "changed_files": execution_input.get("changed_files", []),
            "evidence": {
                "total_items": len(evidence_items),
                "by_kind": dict(kinds),
                "refs": refs,
                "missing": evaluation.get("evidence_missing", []),
            },
            "external_execution": {
                "planned": bool(dispatch_plan),
                "executor": dispatch_plan.get("adapter") or dispatch_result.get("adapter") or "",
                "provider": dispatch_plan.get("provider") or dispatch_result.get("metadata", {}).get("provider", ""),
                "status": dispatch_result.get("status") or dispatch_plan.get("status") or "",
                "planned_command": dispatch_plan.get("planned_command", ""),
                "context_sources": dispatch_result.get("context_sources", dispatch_plan.get("context_sources", [])),
                "required_context": dispatch_plan.get("required_context", []),
                "missing_required_context": dispatch_plan.get("missing_required_context", []),
                "available_context_keys": dispatch_plan.get("available_context_keys", []),
                "capability": dispatch_plan.get("capability", ""),
            "policy_source": dispatch_plan.get("policy_source", "default"),
            "active_policy": dispatch_plan.get("active_policy", {}),
                "alternative_adapters": dispatch_plan.get("alternative_adapters", []),
                "runtime_profile": dispatch_result.get("runtime_profile")
                or dispatch_plan.get("runtime_profile")
                or dispatch_result.get("request_metadata", {}).get("runtime_profile", "")
                or dispatch_plan.get("request_metadata", {}).get("runtime_profile", ""),
                "runtime_provider": dispatch_result.get("runtime_provider")
                or dispatch_plan.get("runtime_provider")
                or dispatch_result.get("request_metadata", {}).get("runtime_provider", "")
                or dispatch_plan.get("request_metadata", {}).get("runtime_provider", ""),
                "plan": {
                    "provider": dispatch_plan.get("provider", ""),
                    "runtime_profile": dispatch_plan.get("runtime_profile")
                    or dispatch_plan.get("request_metadata", {}).get("runtime_profile", ""),
                    "runtime_provider": dispatch_plan.get("runtime_provider")
                    or dispatch_plan.get("request_metadata", {}).get("runtime_provider", ""),
                    "context_sources": dispatch_plan.get("context_sources", []),
                    "status": dispatch_plan.get("status", ""),
                    "planned_command": dispatch_plan.get("planned_command", ""),
                },
                "result": {
                    "provider": dispatch_result.get("metadata", {}).get("provider", ""),
                    "runtime_profile": dispatch_result.get("runtime_profile")
                    or dispatch_result.get("request_metadata", {}).get("runtime_profile", ""),
                    "runtime_provider": dispatch_result.get("runtime_provider")
                    or dispatch_result.get("request_metadata", {}).get("runtime_provider", ""),
                    "context_sources": dispatch_result.get("context_sources", []),
                    "status": dispatch_result.get("status", ""),
                    "notes": dispatch_result.get("notes", ""),
                },
            },
            "external_evidence": {
                "present": bool(external_evidence),
                "event": external_evidence.get("event", ""),
                "refs": external_evidence.get("evidence_refs", []),
                "count": len(external_evidence.get("evidence_refs", [])),
            },
            "ci_result": {
                "present": bool(ci_result),
                "status": ci_result.get("status", ""),
                "ci_ref": ci_result.get("ci_ref", ""),
                "refs": ci_result.get("evidence_refs", []),
            },
            "runtime": {
                "executed": bool(runtime_hooks),
                "event": runtime_hooks.get("event", ""),
                "profile": runtime_hooks.get("profile", "default"),
                "simulated": runtime_hooks.get("simulated"),
                "results": len(runtime_hooks.get("results", [])),
                "context_hints": runtime_hooks.get("context_hints", []),
                "required_context": runtime_hooks.get("required_context", []),
                "missing_context_hints": runtime_hooks.get("missing_context_hints", []),
                "missing_required_context": runtime_hooks.get("missing_required_context", []),
                "available_context_keys": runtime_hooks.get("available_context_keys", []),
                "profile_details": {
                    "provider": runtime_profile.get("provider", ""),
                    "command_examples": runtime_profile.get("command_examples", []),
                    "context_hints": runtime_profile.get("context_hints", {}),
                    "required_context": runtime_profile.get("required_context", {}),
                    "example_contexts": runtime_profile.get("example_contexts", {}),
                    "hook_count": runtime_profile.get("hook_count", len(runtime_profile.get("hooks", []))),
                } if runtime_profile else {},
            },
            "decisions": {
                "guard": guard.get("result"),
                "evaluation": evaluation.get("result"),
                "drift": drift.get("result"),
                "release": release.get("decision"),
            },
            "blockers": blockers,
            "pending_human_action": record.pending_human_action,
            "next_action": record.next_action,
        }

    def get_current_run_id(self) -> str:
        if not self.current_run_file.exists():
            raise FileNotFoundError("Nenhuma run atual encontrada em .cvg-harness/current-run.txt")
        return self.current_run_file.read_text().strip()

    def load_current_run(self) -> OperatorRunRecord:
        return self._load_run_record(self.get_current_run_id())

    def _sync_from_flow(self, record: OperatorRunRecord) -> OperatorRunRecord:
        orch = FlowOrchestrator.load(Path(record.run_workspace))
        orch.context_workspace = self.base_dir
        record.mode = orch.state.mode
        record.current_phase = orch.state.current_phase
        record.current_gate = orch.state.current_gate
        record.current_sprint = orch.state.sprint_id
        if orch.state.status == "completed":
            record.operator_status = "completed"
            record.next_action = "none"
            record.pending_human_action = ""
            record.summary = "run concluída com release readiness aprovado"
        elif orch.state.status == "blocked" and record.operator_status != "paused":
            record.operator_status = "blocked"
            record.next_action = "cvg replan --reason \"...\""
            record.pending_human_action = "review_blocker"
            record.summary = f"fluxo bloqueado em {orch.state.current_gate}"
        self._save_run_record(record)
        return record

    def start_run(self, demand: str, project: Optional[str] = None, mode: str = "AUTO") -> dict:
        project_name = project or self.base_dir.name
        slug = _slugify(demand)[:32]
        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{slug}"
        run_workspace = self._run_dir(run_id)
        dims, rationale = infer_dimensions_from_demand(demand)
        orch = FlowOrchestrator(project_name, demand, "FAST", run_workspace, context_workspace=self.base_dir)
        class_path = orch.classify(dims, rationale)
        with open(class_path) as f:
            classification = json.load(f)
        if mode == "ENTERPRISE":
            classification["mode"] = "ENTERPRISE"
            classification["override_applied"] = True
            classification["override_reason"] = "operator override via cvg run --mode ENTERPRISE"
            Path(class_path).write_text(json.dumps(classification, indent=2))
        orch.mode = classification["mode"]
        orch.state.mode = classification["mode"]
        orch._save_state()
        orch.sync_progress()
        orch.run_research()
        orch.run_prd()
        orch.build_spec()
        orch.run_lint()
        orch.plan_sprints()
        self._append_operator_event(run_workspace, "run_started", {"run_id": run_id})
        self._append_operator_event(run_workspace, "run_ready_for_execution", {"next_action": "approve_sprint"})
        record = OperatorRunRecord(
            run_id=run_id,
            project=project_name,
            demand=demand,
            workspace_root=str(self.root),
            run_workspace=str(run_workspace),
            mode=classification["mode"],
            operator_status="waiting_input",
            next_action="cvg approve",
            pending_human_action="approve_sprint",
            current_phase="sprint",
            current_gate="GATE_5",
            current_sprint=orch.state.sprint_id,
            summary="planejamento concluído; aguardando aprovação humana para iniciar execução controlada",
        )
        self._save_run_record(record)
        return record.to_dict()

    def status(self, run_id: Optional[str] = None) -> dict:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        record = self._sync_from_flow(record)
        blockers = []
        progress_path = Path(record.run_workspace) / "progress.json"
        if progress_path.exists():
            blockers = load_progress(progress_path).blockers
        return {**record.to_dict(), "blockers": blockers}

    def inspect(self, target: Optional[str] = None, run_id: Optional[str] = None) -> dict:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        record = self._sync_from_flow(record)
        run_workspace = Path(record.run_workspace)
        payload = {
            "run": record.to_dict(),
            "artifacts": sorted(p.name for p in (run_workspace / "artifacts").glob("*")),
            "reports": sorted(p.name for p in (run_workspace / "reports").glob("*") if p.is_file() or p.is_dir()),
            "timeline": self._build_timeline(run_workspace),
        }
        sprint_plan_path = run_workspace / "artifacts" / "sprint-plan.json"
        selected_sprint = None
        if sprint_plan_path.exists():
            sprint_plan = json.loads(sprint_plan_path.read_text())
            if target and target.startswith("SPRINT"):
                selected_sprint = next((s for s in sprint_plan.get("sprints", []) if s.get("sprint_id") == target), None)
                payload["sprint"] = selected_sprint
            else:
                payload["sprints"] = sprint_plan.get("sprints", [])
                if record.current_sprint:
                    selected_sprint = next((s for s in sprint_plan.get("sprints", []) if s.get("sprint_id") == record.current_sprint), None)
        for key, rel in {
            "evaluation": "reports/evaluation-report.json",
            "guard": "reports/architecture-guard-report.json",
            "drift": "reports/drift-report.json",
            "release": "reports/release-readiness-report.json",
            "evidence_manifest": "artifacts/evidence-manifest.json",
            "execution_input": "artifacts/execution-input.json",
            "external_dispatch_plan": "artifacts/external-dispatch-plan.json",
            "external_dispatch_result": "reports/external-dispatch-result.json",
            "runtime_hooks": "artifacts/runtime-hooks.json",
            "external_evidence": "artifacts/external-evidence-manifest.json",
            "ci_result": "artifacts/ci-result.json",
        }.items():
            data = self._load_json_if_exists(run_workspace / rel)
            if data is not None:
                payload[key] = data
        if "external_evidence" in payload:
            payload["external_evidence"] = {
                "present": True,
                "event": payload["external_evidence"].get("event", ""),
                "refs": payload["external_evidence"].get("evidence_refs", []),
                "count": len(payload["external_evidence"].get("evidence_refs", [])),
                **payload["external_evidence"],
            }
        if "ci_result" in payload:
            payload["ci_result"] = {
                "present": True,
                **payload["ci_result"],
            }
        payload["known_adapters"] = [adapter.to_dict() for adapter in self._load_executor_registry().list()]
        payload["causal"] = self._build_causal_summary(record, run_workspace, selected_sprint)
        return payload

    def pause(self, run_id: Optional[str] = None) -> dict:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        record.operator_status = "paused"
        record.next_action = "cvg continue"
        record.pending_human_action = "resume_run"
        record.summary = "execução pausada pelo operador"
        self._append_operator_event(Path(record.run_workspace), "operator_paused")
        self._save_run_record(record)
        return record.to_dict()

    def approve(self, sprint_id: Optional[str] = None, run_id: Optional[str] = None) -> dict:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        record = self._sync_from_flow(record)
        if sprint_id and record.current_sprint and sprint_id != record.current_sprint:
            raise ValueError(f"Sprint atual é {record.current_sprint}, não {sprint_id}")
        record.operator_status = "active"
        record.pending_human_action = "provide_execution_inputs"
        record.next_action = "cvg continue --changed-file src/... --evidence evidência-base ou --evidence-file manifest.json"
        record.summary = "sprint aprovada para execução controlada; aguardando changed_files/evidence"
        self._append_operator_event(Path(record.run_workspace), "operator_approved", {"sprint_id": record.current_sprint})
        self._save_run_record(record)
        return record.to_dict()

    def continue_run(self, changed_files=None, evidence=None, evidence_json=None, evidence_file=None, round_num: int = 1, run_id: Optional[str] = None) -> dict:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        orch = FlowOrchestrator.load(Path(record.run_workspace))
        orch.context_workspace = self.base_dir
        if record.operator_status == "paused":
            record.operator_status = "active"
            self._append_operator_event(Path(record.run_workspace), "operator_resumed")
        if record.pending_human_action == "approve_sprint":
            raise ValueError("Run aguardando aprovação humana da sprint atual. Use `cvg approve` primeiro.")

        changed_files = changed_files or []
        evidence_items = self._normalize_evidence_inputs(evidence=evidence, evidence_json=evidence_json, evidence_file=evidence_file)
        evaluator_evidence = self._evidence_strings_for_evaluator(evidence_items)
        outputs: dict[str, object] = {"run": record.to_dict()}

        execution_path, evidence_path = self._save_execution_context(record, changed_files, evidence_items, round_num)
        if changed_files:
            self._append_operator_event(Path(record.run_workspace), "execution_inputs_registered", {"changed_files": changed_files, "round": round_num, "artifact": str(execution_path)})
            outputs["execution_input"] = json.loads(execution_path.read_text())
            outputs["guard"] = orch.check_guard(changed_files)
            if outputs["guard"]["result"] == "FAIL":
                record.operator_status = "blocked"
                record.pending_human_action = "replan_or_fix_scope"
                record.next_action = "cvg replan --reason scope-violated-guard"
                record.summary = "guard reprovou a execução; fluxo bloqueado"
                self._save_run_record(record)
                outputs["run"] = record.to_dict()
                return outputs

        if evidence_items:
            self._append_operator_event(Path(record.run_workspace), "evidence_registered", {"items": len(evidence_items), "artifact": str(evidence_path), "round": round_num})
            outputs["evidence_manifest"] = json.loads(evidence_path.read_text())
            outputs["evaluation"] = orch.evaluate_sprint(
                evidence_files=evaluator_evidence,
                round_num=round_num,
                evidence_items=evidence_items,
            )
            outputs["drift"] = orch.detect_drift()
            outputs["release"] = orch.check_release_readiness()
            record = self._sync_from_flow(record)
            if record.operator_status == "completed":
                record.summary = "run concluída até release readiness"
            elif record.operator_status == "blocked":
                record.pending_human_action = "review_blocker"
                record.next_action = "cvg inspect && cvg replan --reason blocker-review"
                record.summary = "fluxo bloqueado após avaliação/release"
            self._save_run_record(record)
            outputs["run"] = record.to_dict()
            return outputs

        if changed_files:
            record.operator_status = "waiting_input"
            record.pending_human_action = "provide_evidence"
            record.next_action = "cvg continue --evidence evidência-base ou --evidence-file manifest.json"
            record.summary = "guard executado; faltam evidências para avaliação"
        else:
            record.operator_status = "waiting_input"
            record.pending_human_action = "provide_execution_inputs"
            record.next_action = "cvg continue --changed-file src/... --evidence evidência-base"
            record.summary = "run retomada; aguardando changed_files/evidence para seguir o ciclo"
        self._save_run_record(record)
        outputs["run"] = record.to_dict()
        return outputs

    def plan_external_execution(self, executor: Optional[str] = None, execute: bool = False, context: Optional[dict] = None, capability: Optional[str] = None, run_id: Optional[str] = None) -> dict:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        record = self._sync_from_flow(record)
        run_workspace = Path(record.run_workspace)
        sprint_payload = self._current_sprint_payload(run_workspace, record.current_sprint) or {}
        evidence_manifest = self._load_json_if_exists(run_workspace / "artifacts" / "evidence-manifest.json") or {}
        execution_input = self._load_json_if_exists(run_workspace / "artifacts" / "execution-input.json") or {}

        objective = sprint_payload.get("objetivo") or sprint_payload.get("goal") or record.demand
        evidence_targets = []
        for criterion in sprint_payload.get("criterios_aceite", []) or sprint_payload.get("criteria", []) or []:
            if isinstance(criterion, str):
                evidence_targets.append(criterion)
            elif isinstance(criterion, dict) and criterion.get("descricao"):
                evidence_targets.append(criterion["descricao"])

        bridge = ExternalExecutorBridge(self._load_executor_registry())
        selected_adapter = None
        ranked_adapters = []
        if not executor:
            if not capability:
                raise ValueError("Informe --executor ou --capability para preparar o dispatch externo")
            selected_adapter, ranked_adapters = self._select_adapter(run_workspace, capability=capability, context=context)
            executor = selected_adapter["name"]
        adapter = bridge.registry.get(executor)
        if not ranked_adapters:
            ranked_adapters = self._rank_adapters(run_workspace, capability=capability, context=context) if capability else []
        resolved_context, context_sources = self._resolve_dispatch_context(run_workspace, context=context)
        dispatch_context = self._runtime_dispatch_context(run_workspace)
        requirements = self._resolve_dispatch_requirements(adapter, resolved_context)
        if execute and requirements["missing_required_context"]:
            raise ValueError(
                "Execução externa exige contexto obrigatório: " + ", ".join(requirements["missing_required_context"])
            )

        request = ExecutionDispatchRequest(
            run_id=record.run_id,
            sprint_id=record.current_sprint or "SPRINT-1",
            demand=record.demand,
            objective=objective,
            workspace=str(self.base_dir),
            changed_files=execution_input.get("changed_files", []),
            evidence_targets=evidence_targets,
            context=resolved_context,
            context_sources=context_sources,
            metadata={
                "mode": record.mode,
                "evidence_items": len(evidence_manifest.get("items", [])),
                **dispatch_context,
            },
        )
        result = bridge.dispatch(executor, request, execute=execute)

        active_policy, policy_source = self._resolve_capability_policy(capability)
        if selected_adapter:
            active_policy = selected_adapter.get("active_policy", active_policy)
            policy_source = selected_adapter.get("policy_source", policy_source)

        combined_metadata = {**request.metadata, **result.metadata}
        alternative_adapters = [
            {
                "name": item.get("name", ""),
                "provider": item.get("provider", ""),
                "suitability_score": item.get("suitability_score", 0),
                "selection_reason": item.get("selection_reason", []),
                "missing_required_context": item.get("missing_required_context", []),
            }
            for item in ranked_adapters
            if item.get("name") != executor
        ]
        plan_payload = {
            **request.to_dict(),
            **result.to_dict(),
            **requirements,
            "metadata": combined_metadata,
            "request_metadata": request.metadata,
            "result_metadata": result.metadata,
            "runtime_profile": dispatch_context.get("runtime_profile", ""),
            "runtime_provider": dispatch_context.get("runtime_provider", ""),
            "capability": capability or "",
            "policy_source": policy_source,
            "active_policy": active_policy,
            "selection_reason": selected_adapter.get("selection_reason", []) if selected_adapter else self._adapter_selection_reason(adapter, capability, dispatch_context, requirements),
            "suitability_score": selected_adapter.get("suitability_score") if selected_adapter else self._score_adapter(adapter, capability, dispatch_context, requirements),
            "alternative_adapters": alternative_adapters,
            "execute": execute,
        }
        plan_path = run_workspace / "artifacts" / "external-dispatch-plan.json"
        plan_path.write_text(json.dumps(plan_payload, indent=2, ensure_ascii=False))
        self._append_operator_event(run_workspace, "external_executor_planned", {
            "executor": executor,
            "status": result.status,
            "artifact": str(plan_path),
            "provider": requirements["provider"],
            "missing_required_context": requirements["missing_required_context"],
            "runtime_profile": dispatch_context.get("runtime_profile", ""),
            "runtime_provider": dispatch_context.get("runtime_provider", ""),
        })

        if execute and result.status in {"dispatched", "failed"}:
            result_path = run_workspace / "reports" / "external-dispatch-result.json"
            result_payload = {
                **result.to_dict(),
                "context_sources": context_sources,
                "policy_source": policy_source,
                "active_policy": active_policy,
                "runtime_profile": dispatch_context.get("runtime_profile", ""),
                "runtime_provider": dispatch_context.get("runtime_provider", ""),
                "request_metadata": request.metadata,
            }
            result_path.write_text(json.dumps(result_payload, indent=2, ensure_ascii=False))
            if result.status == "dispatched":
                self._append_operator_event(run_workspace, "external_executor_dispatched", {
                    "executor": executor,
                    "status": result.status,
                    "artifact": str(result_path),
                    "provider": requirements["provider"],
                    "runtime_profile": dispatch_context.get("runtime_profile", ""),
                    "runtime_provider": dispatch_context.get("runtime_provider", ""),
                })
            else:
                self._append_operator_event(run_workspace, "external_execution_failed", {
                    "executor": executor,
                    "status": result.status,
                    "artifact": str(result_path),
                    "provider": requirements["provider"],
                    "runtime_profile": dispatch_context.get("runtime_profile", ""),
                    "runtime_provider": dispatch_context.get("runtime_provider", ""),
                })

        record.pending_human_action = "review_external_execution"
        record.next_action = "cvg inspect"
        record.summary = f"dispatch externo preparado para {executor}"
        self._save_run_record(record)
        return {"run": record.to_dict(), "request": request.to_dict(), "plan": plan_payload}

    def list_adapters(self, capability: Optional[str] = None, context: Optional[dict] = None, run_id: Optional[str] = None) -> list[dict]:
        if run_id:
            record = self._load_run_record(run_id)
            run_workspace = Path(record.run_workspace)
        else:
            try:
                record = self.load_current_run()
                run_workspace = Path(record.run_workspace)
            except FileNotFoundError:
                run_workspace = self.base_dir
        return self._rank_adapters(run_workspace, capability=capability, context=context)

    def list_runtime_profiles(self) -> list[dict]:
        return list_runtime_profiles()

    def _resolve_runtime_context_requirements(
        self,
        profile: str,
        hook_event: HookEvent,
        context_payload: dict,
        ci_result: Optional[dict],
        ci_result_json: Optional[str],
        ci_result_file: Optional[str],
        ci_result_url: Optional[str],
    ) -> dict:
        supported_events = get_profile_events(profile)
        if hook_event.value not in supported_events:
            raise ValueError(
                f"Perfil {profile} não suporta o evento {hook_event.value}. Eventos suportados: {supported_events}"
            )

        hints = get_context_hints(profile, hook_event.value)
        required = get_required_context(profile, hook_event.value)
        available_keys = set(context_payload.keys())
        if ci_result is not None:
            available_keys.add("ci_result_json")
        if ci_result_json:
            available_keys.add("ci_result_json")
        if ci_result_file:
            available_keys.add("ci_result_file")
        if ci_result_url:
            available_keys.add("ci_result_url")

        missing_hints = []
        if hints and not any(hint in available_keys for hint in hints):
            missing_hints = hints

        missing_required = [key for key in required if key not in available_keys]

        return {
            "profile": profile,
            "supported_events": supported_events,
            "context_hints": hints,
            "required_context": required,
            "missing_context_hints": missing_hints,
            "missing_required_context": missing_required,
            "available_context_keys": sorted(available_keys),
        }

    def run_runtime_hooks(
        self,
        event: str,
        context: Optional[dict] = None,
        simulated: bool = True,
        profile: str = "default",
        ci_result: Optional[dict] = None,
        ci_result_json: Optional[str] = None,
        ci_result_file: Optional[str] = None,
        ci_result_url: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> dict:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        record = self._sync_from_flow(record)
        run_workspace = Path(record.run_workspace)
        automation = create_automation(profile)
        runtime_profile = get_runtime_profile(profile)
        hook_event = HookEvent(event)
        context_payload = dict(context or {})
        raw_context = dict(context_payload)
        ci_input = {}
        if hook_event == HookEvent.CI_RESULT:
            ci_input = self._normalize_ci_result_input(
                ci_result=ci_result,
                ci_result_json=ci_result_json,
                ci_result_file=ci_result_file,
                ci_result_url=ci_result_url,
            )
        resolved_context = resolve_runtime_context(profile, hook_event.value, context_payload, ci_input or None)
        if hook_event == HookEvent.CI_RESULT and "ci_api" not in resolved_context:
            if ci_result_url:
                resolved_context["ci_api"] = ci_result_url
            elif ci_result_file:
                resolved_context["ci_api"] = Path(ci_result_file).resolve().as_uri()
            elif ci_input.get("ci_ref"):
                resolved_context["ci_api"] = ci_input["ci_ref"]
            else:
                resolved_context["ci_api"] = resolved_context.get("ci_url") or resolved_context.get("ci_run_id") or resolved_context.get("ci_id") or "ci-result"
        runtime_requirements = self._resolve_runtime_context_requirements(
            profile=profile,
            hook_event=hook_event,
            context_payload=resolved_context,
            ci_result=ci_input or None,
            ci_result_json=ci_result_json,
            ci_result_file=ci_result_file,
            ci_result_url=ci_result_url,
        )
        if not simulated and runtime_requirements["missing_required_context"]:
            raise ValueError(
                "Execução real de runtime exige contexto obrigatório: "
                + ", ".join(runtime_requirements["missing_required_context"])
            )
        executor = RuntimeExecutor(automation, simulated=simulated)
        results = executor.run_hooks(hook_event, resolved_context)
        artifact_path = run_workspace / "artifacts" / "runtime-hooks.json"
        external_evidence_path = run_workspace / "artifacts" / "external-evidence-manifest.json"
        ci_result_path = run_workspace / "artifacts" / "ci-result.json"
        evidence_refs: list[str] = []
        if automation.external_evidence_refs:
            for result in results:
                artifact_output = result.get("artifact_output")
                if artifact_output and artifact_output not in evidence_refs:
                    evidence_refs.append(str(artifact_output))
                external_ref = result.get("external_ref")
                if external_ref and external_ref not in evidence_refs:
                    evidence_refs.append(str(external_ref))
        ci_payload = None
        if hook_event == HookEvent.CI_RESULT:
            ci_ref = ci_input.get("ci_ref") or resolved_context.get("ci_url") or resolved_context.get("ci_run_id") or resolved_context.get("ci_id") or "ci-result"
            ci_status = ci_input.get("status") or resolved_context.get("ci_status") or (results[0].get("status") if results else "unknown")
            for ref in ci_input.get("evidence_refs", []):
                if ref not in evidence_refs:
                    evidence_refs.append(ref)
            ci_payload = {
                "run_id": record.run_id,
                "event": hook_event.value,
                "profile": automation.profile,
                "provider": runtime_profile.get("provider", ""),
                "simulated": simulated,
                "context": resolved_context,
                "raw_context": raw_context,
                "status": ci_status,
                "ci_ref": str(ci_ref),
                "evidence_refs": evidence_refs or [str(ci_ref)],
                "results": results,
                "source": ci_input.get("source", "external_ci"),
                "metadata": ci_input.get("metadata", {}),
                "updated_at": _now(),
            }
            ci_result_path.write_text(json.dumps(ci_payload, indent=2, ensure_ascii=False))
            if str(ci_ref) not in evidence_refs:
                evidence_refs.append(str(ci_ref))
        payload = {
            "run_id": record.run_id,
            "event": hook_event.value,
            "profile": automation.profile,
            "provider": runtime_profile.get("provider", ""),
            "simulated": simulated,
            "context": resolved_context,
            "raw_context": raw_context,
            "context_hints": runtime_requirements["context_hints"],
            "required_context": runtime_requirements["required_context"],
            "missing_context_hints": runtime_requirements["missing_context_hints"],
            "missing_required_context": runtime_requirements["missing_required_context"],
            "available_context_keys": runtime_requirements["available_context_keys"],
            "results": results,
            "external_evidence_refs": evidence_refs,
            "resolved_context": resolved_context,
            "updated_at": _now(),
        }
        artifact_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        external_payload = {
            "run_id": record.run_id,
            "event": hook_event.value,
            "simulated": simulated,
            "evidence_refs": evidence_refs,
            "results": results,
            "updated_at": _now(),
        }
        external_evidence_path.write_text(json.dumps(external_payload, indent=2, ensure_ascii=False))
        self._append_operator_event(run_workspace, "runtime_hooks_executed", {
            "event": hook_event.value,
            "profile": automation.profile,
            "provider": runtime_profile.get("provider", ""),
            "simulated": simulated,
            "missing_context_hints": runtime_requirements["missing_context_hints"],
            "artifact": str(artifact_path),
        })
        if evidence_refs:
            self._append_operator_event(run_workspace, "external_evidence_registered", {
                "event": hook_event.value,
                "count": len(evidence_refs),
                "artifact": str(external_evidence_path),
            })
        if ci_payload is not None:
            self._append_operator_event(run_workspace, "ci_result_registered", {
                "event": hook_event.value,
                "profile": automation.profile,
                "provider": runtime_profile.get("provider", ""),
                "status": ci_payload["status"],
                "artifact": str(ci_result_path),
                "ci_ref": ci_payload["ci_ref"],
            })
        record.pending_human_action = "review_runtime_hooks"
        record.next_action = "cvg inspect"
        record.summary = f"runtime hooks executados para {hook_event.value}"
        self._save_run_record(record)
        return {
            "run": record.to_dict(),
            "runtime_hooks": payload,
            "external_evidence": external_payload,
            "ci_result": ci_payload,
        }

    def replan(self, reason: str, run_id: Optional[str] = None) -> dict:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        decision = ReplanCoordinator().evaluate(trigger=ReplanTrigger.MANUAL_REQUEST.value, context={"reason": reason})
        decision.reason = reason
        output_path = Path(record.run_workspace) / "artifacts" / "replan-decision.json"
        save_replan_decision(decision, output_path)
        self._append_operator_event(Path(record.run_workspace), "operator_replanned", {"reason": reason, "action": decision.action, "artifact": str(output_path)})
        record.operator_status = "blocked"
        record.pending_human_action = "review_replan"
        record.next_action = "cvg inspect"
        record.summary = f"replan manual registrado: {reason}"
        self._save_run_record(record)
        return {"run": record.to_dict(), "decision": decision.to_dict()}

    def events(self, limit: int = 20, event_type: Optional[str] = None, run_id: Optional[str] = None) -> list[dict]:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        return [event.to_dict() for event in load_events(Path(record.run_workspace) / "event-log.jsonl", event_type=event_type)[-limit:]]

    def metrics(self, run_id: Optional[str] = None) -> dict:
        record = self._load_run_record(run_id) if run_id else self.load_current_run()
        run_workspace = Path(record.run_workspace)
        output_path = run_workspace / "delivery-metrics.json"
        agg = MetricsAggregator()
        metrics = agg.export_delivery_metrics(
            project=record.project,
            feature=record.demand,
            mode=record.mode,
            output_path=output_path,
            event_log_path=run_workspace / "event-log.jsonl",
            progress_path=run_workspace / "progress.json" if (run_workspace / "progress.json").exists() else None,
        )
        return metrics.to_dict()
