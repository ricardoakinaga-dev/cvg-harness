"""
P3-4: Automação mais profunda do runtime
Automação que conecta o harness a execução real (hooks, CI, evidências externas).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional
import re


class HookEvent(Enum):
    PRE_GATE = "pre_gate"
    POST_GATE = "post_gate"
    PRE_SPRINT = "pre_sprint"
    POST_SPRINT = "post_sprint"
    EVALUATION_TRIGGER = "evaluation_trigger"
    LINT_TRIGGER = "lint_trigger"
    ARCH_GUARD_TRIGGER = "arch_guard_trigger"
    DRIFT_CHECK = "drift_check"
    CI_RESULT = "ci_result"


@dataclass
class RuntimeHook:
    event: str
    command: str
    artifact_output: Optional[str] = None
    timeout_seconds: int = 300
    required: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RuntimeAutomation:
    hooks: dict[str, list[RuntimeHook]] = field(default_factory=dict)
    ci_integration_enabled: bool = False
    external_evidence_refs: bool = True
    profile: str = "default"
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def register_hook(self, event: HookEvent, hook: RuntimeHook) -> None:
        if event.value not in self.hooks:
            self.hooks[event.value] = []
        self.hooks[event.value].append(hook)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_hooks(self, event: HookEvent) -> list[RuntimeHook]:
        return self.hooks.get(event.value, [])


class RuntimeExecutor:
    """
    Executa hooks registrados e integra resultados externos.
    Não substitui decisões documentais - apenas as informa.
    """

    def __init__(self, automation: RuntimeAutomation, simulated: bool = False):
        self.automation = automation
        self.simulated = simulated

    def run_hooks(self, event: HookEvent, context: dict) -> list[dict]:
        results = []
        hooks = self.automation.get_hooks(event)
        for hook in hooks:
            result = self._execute_hook(hook, context)
            results.append(result)
        return results

    def _execute_hook(self, hook: RuntimeHook, context: dict) -> dict:
        cmd = hook.command
        for key, value in context.items():
            cmd = cmd.replace(f"{{{key}}}", str(value))

        if self.simulated:
            return {
                "hook_event": hook.event,
                "command": cmd,
                "status": "simulated",
                "artifact_output": hook.artifact_output,
                "reason": "Execução simulada - definir simulated=False para execução real",
            }

        import subprocess
        import shlex

        try:
            result = subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                text=True,
                timeout=hook.timeout_seconds,
            )
            return {
                "hook_event": hook.event,
                "command": cmd,
                "status": "success" if result.returncode == 0 else "failed",
                "artifact_output": hook.artifact_output,
                "return_code": result.returncode,
                "stdout": result.stdout[:500] if result.stdout else "",
                "stderr": result.stderr[:500] if result.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {
                "hook_event": hook.event,
                "command": cmd,
                "status": "timeout",
                "artifact_output": hook.artifact_output,
                "reason": f"Comando excedeu timeout de {hook.timeout_seconds}s",
            }
        except Exception as e:
            return {
                "hook_event": hook.event,
                "command": cmd,
                "status": "error",
                "artifact_output": hook.artifact_output,
                "reason": str(e),
            }


DEFAULT_HOOKS = {
    HookEvent.LINT_TRIGGER: RuntimeHook(
        event="lint_trigger",
        command="python -m py_compile {artifact}",
        artifact_output="lint-output.json",
        required=False,
    ),
    HookEvent.EVALUATION_TRIGGER: RuntimeHook(
        event="evaluation_trigger",
        command="pytest {test_path} --json-report",
        artifact_output="test-report.json",
        required=True,
    ),
    HookEvent.CI_RESULT: RuntimeHook(
        event="ci_result",
        command="curl -s {ci_api}",
        artifact_output="ci-result.json",
        required=False,
    ),
}

PROFILE_HOOKS = {
    "default": {
        HookEvent.LINT_TRIGGER: DEFAULT_HOOKS[HookEvent.LINT_TRIGGER],
        HookEvent.EVALUATION_TRIGGER: DEFAULT_HOOKS[HookEvent.EVALUATION_TRIGGER],
        HookEvent.CI_RESULT: DEFAULT_HOOKS[HookEvent.CI_RESULT],
    },
    "ci-readonly": {
        HookEvent.CI_RESULT: RuntimeHook(
            event="ci_result",
            command="curl -s {ci_result_url}",
            artifact_output="ci-result.json",
            required=False,
        ),
    },
    "quality-gates": {
        HookEvent.LINT_TRIGGER: DEFAULT_HOOKS[HookEvent.LINT_TRIGGER],
        HookEvent.EVALUATION_TRIGGER: DEFAULT_HOOKS[HookEvent.EVALUATION_TRIGGER],
        HookEvent.CI_RESULT: RuntimeHook(
            event="ci_result",
            command="gh run view {ci_run_id} --repo {repository} --json conclusion,url,workflowName",
            artifact_output="ci-result.json",
            required=False,
        ),
    },
    "github-actions": {
        HookEvent.CI_RESULT: RuntimeHook(
            event="ci_result",
            command="gh run view {ci_run_id} --repo {repository} --json conclusion,url,workflowName",
            artifact_output="ci-result.json",
            required=False,
        ),
    },
    "gitlab-ci": {
        HookEvent.CI_RESULT: RuntimeHook(
            event="ci_result",
            command="curl -s {ci_api}",
            artifact_output="ci-result.json",
            required=False,
        ),
    },
    "azure-pipelines": {
        HookEvent.CI_RESULT: RuntimeHook(
            event="ci_result",
            command="az pipelines runs show --id {build_id} --org {organization} --project {project}",
            artifact_output="ci-result.json",
            required=False,
        ),
    },
}

RUNTIME_PROFILES = {
    "default": {
        "description": "Perfil padrão com lint, evaluation e CI result opt-in.",
        "hooks": [HookEvent.LINT_TRIGGER, HookEvent.EVALUATION_TRIGGER, HookEvent.CI_RESULT],
        "provider": "generic",
        "command_examples": ["python -m py_compile {artifact}", "pytest {test_path} --json-report", "curl -s {ci_api}"],
        "context_hints": {
            "lint_trigger": ["artifact"],
            "evaluation_trigger": ["test_path"],
            "ci_result": ["ci_api", "ci_url", "ci_run_id"],
        },
        "required_context": {
            "lint_trigger": ["artifact"],
            "evaluation_trigger": ["test_path"],
            "ci_result": ["ci_api"],
        },
        "example_contexts": {
            "lint_trigger": [{"artifact": "src/module.py"}],
            "evaluation_trigger": [{"test_path": "tests/test_module.py"}],
            "ci_result": [{"ci_api": "https://ci.example/api/runs/42"}],
        },
    },
    "ci-readonly": {
        "description": "Perfil mínimo focado em coleta de resultado de CI.",
        "hooks": [HookEvent.CI_RESULT],
        "provider": "generic-ci",
        "command_examples": ["curl -s {ci_result_url}"],
        "context_hints": {
            "ci_result": ["ci_result_url", "ci_result_file", "ci_result_json"],
        },
        "required_context": {
            "ci_result": ["ci_result_url"],
        },
        "example_contexts": {
            "ci_result": [{"ci_result_url": "https://ci.example/runs/42"}],
        },
    },
    "quality-gates": {
        "description": "Perfil voltado a validações de qualidade locais e CI.",
        "hooks": [HookEvent.LINT_TRIGGER, HookEvent.EVALUATION_TRIGGER, HookEvent.CI_RESULT],
        "provider": "local-ci",
        "command_examples": ["gh run view {ci_run_id} --repo {repository} --json conclusion,url,workflowName"],
        "context_hints": {
            "lint_trigger": ["artifact"],
            "evaluation_trigger": ["test_path"],
            "ci_result": ["ci_run_id", "repository", "ci_result_url"],
        },
        "required_context": {
            "lint_trigger": ["artifact"],
            "evaluation_trigger": ["test_path"],
            "ci_result": ["repository", "ci_run_id"],
        },
        "example_contexts": {
            "ci_result": [{"repository": "openai/cvg-harness", "ci_run_id": "42", "workflow": "tests"}],
        },
    },
    "github-actions": {
        "description": "Perfil orientado a GitHub Actions e coleta de conclusão de workflow.",
        "hooks": [HookEvent.CI_RESULT],
        "provider": "github-actions",
        "command_examples": ["gh run view {ci_run_id} --repo {repository} --json conclusion,url,workflowName"],
        "context_hints": {
            "ci_result": ["ci_run_id", "repository", "workflow", "ci_url"],
        },
        "required_context": {
            "ci_result": ["ci_run_id", "repository"],
        },
        "example_contexts": {
            "ci_result": [{"repository": "openai/cvg-harness", "ci_run_id": "42", "workflow": "tests", "ci_url": "https://github.com/openai/cvg-harness/actions/runs/42"}],
        },
    },
    "gitlab-ci": {
        "description": "Perfil orientado a GitLab CI com coleta remota de resultado.",
        "hooks": [HookEvent.CI_RESULT],
        "provider": "gitlab-ci",
        "command_examples": ["curl -s {ci_api}"],
        "context_hints": {
            "ci_result": ["ci_api", "ci_result_url", "ci_job_id"],
        },
        "required_context": {
            "ci_result": ["ci_api"],
        },
        "example_contexts": {
            "ci_result": [{"ci_api": "https://gitlab.example/api/v4/projects/123/jobs/456"}],
        },
    },
    "azure-pipelines": {
        "description": "Perfil orientado a Azure Pipelines com contexto resolvido de build.",
        "hooks": [HookEvent.CI_RESULT],
        "provider": "azure-pipelines",
        "command_examples": ["az pipelines runs show --id {build_id} --org {organization} --project {project}"],
        "context_hints": {
            "ci_result": ["organization", "project", "build_id", "ci_api", "ci_result_url"],
        },
        "required_context": {
            "ci_result": ["organization", "project", "build_id"],
        },
        "example_contexts": {
            "ci_result": [{"organization": "openai", "project": "cvg-harness", "build_id": "42", "ci_url": "https://dev.azure.com/openai/cvg-harness/_build/results?buildId=42"}],
        },
    },
}


def get_runtime_profile(profile: str) -> dict:
    if profile not in RUNTIME_PROFILES:
        raise ValueError(f"Perfil de runtime desconhecido: {profile}")
    return RUNTIME_PROFILES[profile]


def get_profile_events(profile: str) -> list[str]:
    return [event.value for event in get_runtime_profile(profile)["hooks"]]


def get_context_hints(profile: str, event: str) -> list[str]:
    return list(get_runtime_profile(profile).get("context_hints", {}).get(event, []))


def list_runtime_profiles() -> list[dict]:
    return [
        {
            "name": name,
            "description": data["description"],
            "events": [event.value for event in data["hooks"]],
            "hook_count": len(data["hooks"]),
            "context_hints": data.get("context_hints", {}),
            "required_context": data.get("required_context", {}),
            "example_contexts": data.get("example_contexts", {}),
            "provider": data.get("provider", ""),
            "command_examples": data.get("command_examples", []),
        }
        for name, data in RUNTIME_PROFILES.items()
    ]


def resolve_runtime_context(profile: str, event: str, context: Optional[dict] = None, ci_result: Optional[dict] = None) -> dict:
    resolved = dict(context or {})
    payload = ci_result or {}
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

    for source in (payload, metadata):
        if not isinstance(source, dict):
            continue
        for key in ("ci_ref", "ci_url", "ci_result_url", "ci_api", "ci_run_id", "ci_id", "repository", "workflow", "job", "branch", "sha", "ci_job_id", "project_id"):
            value = source.get(key)
            if value is not None and key not in resolved:
                resolved[key] = value

    if profile in {"github-actions", "quality-gates"} and event == HookEvent.CI_RESULT.value:
        ref = str(resolved.get("ci_ref") or resolved.get("ci_url") or resolved.get("ci_result_url") or payload.get("ci_ref") or payload.get("ci_url") or payload.get("ci_result_url") or "")
        match = re.search(r"github\.com/([^/]+/[^/]+)/actions/runs/(\d+)", ref)
        if match:
            resolved.setdefault("repository", match.group(1))
            resolved.setdefault("ci_run_id", match.group(2))
            resolved.setdefault("ci_url", ref)
            resolved.setdefault("ci_api", f"https://api.github.com/repos/{match.group(1)}/actions/runs/{match.group(2)}")
        elif resolved.get("repository") and resolved.get("ci_run_id"):
            resolved.setdefault("ci_api", f"https://api.github.com/repos/{resolved['repository']}/actions/runs/{resolved['ci_run_id']}")

    elif profile == "gitlab-ci" and event == HookEvent.CI_RESULT.value:
        ref = str(resolved.get("ci_api") or resolved.get("ci_result_url") or payload.get("ci_ref") or payload.get("ci_url") or payload.get("ci_result_url") or "")
        if ref:
            resolved.setdefault("ci_api", ref)
            resolved.setdefault("ci_result_url", ref)
    elif profile == "azure-pipelines" and event == HookEvent.CI_RESULT.value:
        ref = str(
            resolved.get("ci_url")
            or resolved.get("ci_result_url")
            or resolved.get("ci_ref")
            or payload.get("ci_url")
            or payload.get("ci_result_url")
            or payload.get("ci_ref")
            or ""
        )
        match = re.search(r"dev\.azure\.com/([^/]+)/([^/]+)/(?:_build/results\?buildId=|_apis/build/builds/)(\d+)", ref)
        if match:
            resolved.setdefault("organization", match.group(1))
            resolved.setdefault("project", match.group(2))
            resolved.setdefault("build_id", match.group(3))
            resolved.setdefault(
                "ci_api",
                f"https://dev.azure.com/{match.group(1)}/{match.group(2)}/_apis/build/builds/{match.group(3)}?api-version=7.1-preview.7",
            )
            resolved.setdefault("ci_url", ref)
        elif resolved.get("organization") and resolved.get("project") and resolved.get("build_id"):
            resolved.setdefault(
                "ci_api",
                f"https://dev.azure.com/{resolved['organization']}/{resolved['project']}/_apis/build/builds/{resolved['build_id']}?api-version=7.1-preview.7",
            )

    return resolved


def get_required_context(profile: str, event: str) -> list[str]:
    return list(get_runtime_profile(profile).get("required_context", {}).get(event, []))


def get_example_contexts(profile: str, event: str) -> list[dict]:
    return list(get_runtime_profile(profile).get("example_contexts", {}).get(event, []))


def create_automation(profile: str = "default") -> RuntimeAutomation:
    if profile not in RUNTIME_PROFILES:
        raise ValueError(f"Perfil de runtime desconhecido: {profile}")
    auto = RuntimeAutomation(ci_integration_enabled=True, external_evidence_refs=True, profile=profile)
    for event, hook in PROFILE_HOOKS[profile].items():
        auto.register_hook(event, hook)
    return auto


def create_default_automation() -> RuntimeAutomation:
    return create_automation("default")


def save_automation(automation: RuntimeAutomation, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(automation.to_dict(), f, indent=2)


def load_automation(path: Path) -> RuntimeAutomation:
    with open(path) as f:
        data = json.load(f)
    hooks = {}
    for event, hook_list in data.get("hooks", {}).items():
        hooks[event] = [RuntimeHook(**h) for h in hook_list]
    data["hooks"] = hooks
    return RuntimeAutomation(**data)
