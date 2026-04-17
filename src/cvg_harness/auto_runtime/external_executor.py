"""
Contratos para executores externos reais.
Preservam a separação entre orquestrador (harness) e executor.
"""

from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ExternalExecutionSignal:
    executor: str
    dispatch_ref: str
    status: str
    external: bool = True
    notes: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExternalExecutorAdapter:
    name: str
    transport: str  # manual | cli | webhook
    entrypoint: str
    capabilities: list[str] = field(default_factory=list)
    emits_evidence: bool = True
    requires_human_approval: bool = True
    description: str = ""
    provider: str = ""
    context_hints: list[str] = field(default_factory=list)
    required_context: list[str] = field(default_factory=list)
    example_contexts: list[dict] = field(default_factory=list)
    command_examples: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExecutionDispatchRequest:
    run_id: str
    sprint_id: str
    demand: str
    objective: str
    workspace: str
    changed_files: list[str] = field(default_factory=list)
    evidence_targets: list[str] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    context_sources: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExecutionDispatchResult:
    adapter: str
    status: str  # planned | manual_required | dispatched | failed
    planned_command: str = ""
    external_ref: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    notes: str = ""
    metadata: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExternalExecutorRegistry:
    adapters: dict[str, ExternalExecutorAdapter] = field(default_factory=dict)

    def register(self, adapter: ExternalExecutorAdapter) -> None:
        self.adapters[adapter.name] = adapter

    def get(self, name: str) -> ExternalExecutorAdapter:
        if name not in self.adapters:
            raise KeyError(f"Adapter externo não encontrado: {name}")
        return self.adapters[name]

    def list(self) -> list[ExternalExecutorAdapter]:
        return list(self.adapters.values())

    def to_dict(self) -> dict:
        return {"adapters": {name: adapter.to_dict() for name, adapter in self.adapters.items()}}


class ExternalExecutorBridge:
    """
    Prepara ou despacha execução para adaptadores externos.
    O harness continua sendo o orquestrador; o executor é explícito e opt-in.
    """

    def __init__(self, registry: ExternalExecutorRegistry):
        self.registry = registry

    def _render_entrypoint(self, adapter: ExternalExecutorAdapter, request: ExecutionDispatchRequest) -> str:
        payload = request.to_dict()
        payload["changed_files"] = ",".join(request.changed_files)
        payload["evidence_targets"] = ",".join(request.evidence_targets)
        for key, value in request.context.items():
            if isinstance(value, (str, int, float, bool)):
                payload[key] = value
        command = adapter.entrypoint
        for key, value in payload.items():
            command = command.replace(f"{{{key}}}", str(value))
        return command

    def plan(self, adapter_name: str, request: ExecutionDispatchRequest) -> ExecutionDispatchResult:
        adapter = self.registry.get(adapter_name)
        command = self._render_entrypoint(adapter, request)
        status = "manual_required" if adapter.requires_human_approval or adapter.transport == "manual" else "planned"
        notes = "Execução externa preparada; dispatch explícito continua opt-in"
        return ExecutionDispatchResult(
            adapter=adapter.name,
            status=status,
            planned_command=command,
            notes=notes,
            metadata={
                "transport": adapter.transport,
                "capabilities": adapter.capabilities,
                "emits_evidence": adapter.emits_evidence,
                "provider": adapter.provider,
                "context_hints": adapter.context_hints,
                "required_context": adapter.required_context,
                "example_contexts": adapter.example_contexts,
                "command_examples": adapter.command_examples,
            },
        )

    def dispatch(self, adapter_name: str, request: ExecutionDispatchRequest, execute: bool = False) -> ExecutionDispatchResult:
        adapter = self.registry.get(adapter_name)
        planned = self.plan(adapter_name, request)
        if not execute:
            return planned
        if adapter.transport != "cli":
            planned.status = "manual_required"
            planned.notes = "Somente adapters transport=cli podem ser executados diretamente pelo bridge"
            return planned

        try:
            completed = subprocess.run(
                shlex.split(planned.planned_command),
                capture_output=True,
                text=True,
                timeout=300,
            )
        except Exception as exc:
            return ExecutionDispatchResult(
                adapter=adapter.name,
                status="failed",
                planned_command=planned.planned_command,
                notes=str(exc),
                metadata={"transport": adapter.transport},
            )

        status = "dispatched" if completed.returncode == 0 else "failed"
        return ExecutionDispatchResult(
            adapter=adapter.name,
            status=status,
            planned_command=planned.planned_command,
            external_ref="",
            notes=(completed.stdout or completed.stderr or "").strip()[:500],
            metadata={
                "transport": adapter.transport,
                "return_code": completed.returncode,
            },
        )


def create_default_executor_registry() -> ExternalExecutorRegistry:
    registry = ExternalExecutorRegistry()
    registry.register(
        ExternalExecutorAdapter(
            name="manual-review",
            transport="manual",
            entrypoint="manual://handoff/{run_id}/{sprint_id}",
            capabilities=["planning", "review"],
            requires_human_approval=True,
            description="Handoff manual para executor humano ou sistema externo fora da CLI.",
            provider="human-review",
            context_hints=["repository", "ci_ref", "ci_status"],
            example_contexts=[{"repository": "openai/cvg-harness", "ci_ref": "https://github.com/openai/cvg-harness/actions/runs/77"}],
            command_examples=["manual://handoff/{run_id}/{sprint_id}"],
        )
    )
    registry.register(
        ExternalExecutorAdapter(
            name="local-cli",
            transport="cli",
            entrypoint="echo dispatch {run_id} {sprint_id}",
            capabilities=["code", "tests"],
            requires_human_approval=False,
            description="Adapter local de exemplo para dispatch explícito via CLI.",
            provider="local-cli",
            context_hints=["repository", "ci_run_id", "ci_api"],
            example_contexts=[{"repository": "openai/cvg-harness", "ci_run_id": "77"}],
            command_examples=["echo dispatch {run_id} {sprint_id}"],
        )
    )
    registry.register(
        ExternalExecutorAdapter(
            name="github-actions-review",
            transport="cli",
            entrypoint="gh run view {ci_run_id} --repo {repository} --json conclusion,url,workflowName",
            capabilities=["ci", "review", "evidence"],
            requires_human_approval=False,
            description="Adapter CLI para inspecionar contexto operacional vindo de GitHub Actions.",
            provider="github-actions",
            context_hints=["repository", "ci_run_id", "ci_ref"],
            required_context=["repository", "ci_run_id"],
            example_contexts=[{"repository": "openai/cvg-harness", "ci_run_id": "77"}],
            command_examples=["gh run view {ci_run_id} --repo {repository} --json conclusion,url,workflowName"],
        )
    )
    registry.register(
        ExternalExecutorAdapter(
            name="gitlab-ci-review",
            transport="cli",
            entrypoint="curl -s {ci_api}",
            capabilities=["ci", "review", "evidence"],
            requires_human_approval=False,
            description="Adapter CLI para inspecionar contexto operacional vindo de GitLab CI.",
            provider="gitlab-ci",
            context_hints=["ci_api", "ci_ref"],
            required_context=["ci_api"],
            example_contexts=[{"ci_api": "https://gitlab.example/api/v4/projects/123/jobs/456"}],
            command_examples=["curl -s {ci_api}"],
        )
    )
    return registry


def save_executor_registry(registry: ExternalExecutorRegistry, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry.to_dict(), indent=2))


def load_executor_registry(path: Path) -> ExternalExecutorRegistry:
    data = json.loads(path.read_text())
    registry = ExternalExecutorRegistry()
    for name, payload in data.get("adapters", {}).items():
        registry.register(ExternalExecutorAdapter(name=name, **{k: v for k, v in payload.items() if k != "name"}))
    return registry
