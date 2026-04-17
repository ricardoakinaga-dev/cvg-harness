"""
Tests for RuntimeExecutor, runtime automation and external executor contracts.
Covers PR-06 runtime integration requirements.
"""
import subprocess
import tempfile
from pathlib import Path

import pytest

from cvg_harness.auto_runtime.external_executor import (
    ExternalExecutorAdapter,
    ExecutionDispatchRequest,
    ExternalExecutorRegistry,
    ExternalExecutorBridge,
    create_default_executor_registry,
    save_executor_registry,
    load_executor_registry,
)
from cvg_harness.auto_runtime.runtime_automation import (
    RuntimeAutomation,
    RuntimeExecutor,
    RuntimeHook,
    HookEvent,
    create_default_automation,
    create_automation,
    resolve_runtime_context,
    list_runtime_profiles,
    save_automation,
    load_automation,
)


class TestRuntimeHook:
    def test_hook_to_dict(self):
        hook = RuntimeHook(
            event="lint_trigger",
            command="pytest {test_path}",
            artifact_output="lint-output.json",
            timeout_seconds=60,
            required=True,
        )
        d = hook.to_dict()
        assert d["event"] == "lint_trigger"
        assert d["command"] == "pytest {test_path}"
        assert d["artifact_output"] == "lint-output.json"
        assert d["timeout_seconds"] == 60
        assert d["required"] is True

    def test_hook_default_values(self):
        hook = RuntimeHook(event="pre_gate", command="echo test")
        assert hook.artifact_output is None
        assert hook.timeout_seconds == 300
        assert hook.required is False


class TestRuntimeAutomation:
    def test_register_hook(self):
        auto = RuntimeAutomation()
        hook = RuntimeHook(event="pre_gate", command="echo pre")
        auto.register_hook(HookEvent.PRE_GATE, hook)
        hooks = auto.get_hooks(HookEvent.PRE_GATE)
        assert len(hooks) == 1
        assert hooks[0].command == "echo pre"

    def test_get_hooks_empty(self):
        auto = RuntimeAutomation()
        hooks = auto.get_hooks(HookEvent.PRE_GATE)
        assert hooks == []

    def test_create_default_automation(self):
        auto = create_default_automation()
        assert auto.ci_integration_enabled is True
        assert auto.external_evidence_refs is True
        assert len(auto.get_hooks(HookEvent.LINT_TRIGGER)) == 1
        assert len(auto.get_hooks(HookEvent.EVALUATION_TRIGGER)) == 1

    def test_create_profiled_automation(self):
        auto = create_automation('ci-readonly')
        assert auto.profile == 'ci-readonly'
        assert len(auto.get_hooks(HookEvent.CI_RESULT)) == 1
        assert auto.get_hooks(HookEvent.LINT_TRIGGER) == []

    def test_create_github_actions_profile(self):
        auto = create_automation('github-actions')
        assert auto.profile == 'github-actions'
        assert len(auto.get_hooks(HookEvent.CI_RESULT)) == 1
        assert auto.get_hooks(HookEvent.LINT_TRIGGER) == []

    def test_list_runtime_profiles(self):
        profiles = list_runtime_profiles()
        names = {profile['name'] for profile in profiles}
        assert {'default', 'ci-readonly', 'quality-gates', 'github-actions', 'gitlab-ci', 'azure-pipelines'} <= names
        ci_profile = next(profile for profile in profiles if profile['name'] == 'ci-readonly')
        assert ci_profile['hook_count'] == 1
        assert 'ci_result' in ci_profile['context_hints']
        gh_profile = next(profile for profile in profiles if profile['name'] == 'github-actions')
        assert gh_profile['provider'] == 'github-actions'
        assert any('gh run view' in cmd for cmd in gh_profile['command_examples'])
        assert gh_profile['required_context']['ci_result'] == ['ci_run_id', 'repository']
        assert gh_profile['example_contexts']['ci_result'][0]['repository'] == 'openai/cvg-harness'
        az_profile = next(profile for profile in profiles if profile['name'] == 'azure-pipelines')
        assert az_profile['provider'] == 'azure-pipelines'
        assert az_profile['required_context']['ci_result'] == ['organization', 'project', 'build_id']
        assert 'az pipelines runs show' in az_profile['command_examples'][0]

    def test_resolve_runtime_context_from_github_actions_ci_result(self):
        context = resolve_runtime_context(
            'github-actions',
            'ci_result',
            {},
            {
                'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42',
                'metadata': {'workflow': 'tests'},
            },
        )
        assert context['repository'] == 'openai/cvg-harness'
        assert context['ci_run_id'] == '42'
        assert context['ci_api'] == 'https://api.github.com/repos/openai/cvg-harness/actions/runs/42'
        assert context['workflow'] == 'tests'

    def test_resolve_runtime_context_from_gitlab_ci_result(self):
        context = resolve_runtime_context(
            'gitlab-ci',
            'ci_result',
            {},
            {
                'ci_result_url': 'https://gitlab.example/api/v4/projects/123/jobs/456',
                'metadata': {'ci_job_id': '456'},
            },
        )
        assert context['ci_api'] == 'https://gitlab.example/api/v4/projects/123/jobs/456'
        assert context['ci_result_url'] == 'https://gitlab.example/api/v4/projects/123/jobs/456'
        assert context['ci_job_id'] == '456'

    def test_resolve_runtime_context_from_azure_pipelines_ci_result(self):
        context = resolve_runtime_context(
            'azure-pipelines',
            'ci_result',
            {},
            {
                'ci_ref': 'https://dev.azure.com/openai/cvg-harness/_build/results?buildId=42',
            },
        )
        assert context['organization'] == 'openai'
        assert context['project'] == 'cvg-harness'
        assert context['build_id'] == '42'
        assert context['ci_api'] == 'https://dev.azure.com/openai/cvg-harness/_apis/build/builds/42?api-version=7.1-preview.7'

    def test_automation_persistence(self):
        auto = create_default_automation()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
            path = Path(f.name)
        try:
            save_automation(auto, path)
            loaded = load_automation(path)
            assert loaded.ci_integration_enabled == auto.ci_integration_enabled
            assert len(loaded.get_hooks(HookEvent.LINT_TRIGGER)) == 1
        finally:
            path.unlink()


class TestRuntimeExecutor:
    def test_run_hooks_empty(self):
        auto = RuntimeAutomation()
        executor = RuntimeExecutor(auto, simulated=True)
        results = executor.run_hooks(HookEvent.PRE_GATE, {})
        assert results == []

    def test_simulated_hook_execution(self):
        auto = RuntimeAutomation()
        hook = RuntimeHook(event="pre_gate", command="echo test", required=False)
        auto.register_hook(HookEvent.PRE_GATE, hook)
        executor = RuntimeExecutor(auto, simulated=True)
        results = executor.run_hooks(HookEvent.PRE_GATE, {})
        assert len(results) == 1
        assert results[0]["status"] == "simulated"
        assert "Execução simulada" in results[0]["reason"]

    def test_simulated_multiple_hooks(self):
        auto = RuntimeAutomation()
        auto.register_hook(HookEvent.PRE_GATE, RuntimeHook(event="pre_gate", command="echo 1"))
        auto.register_hook(HookEvent.POST_GATE, RuntimeHook(event="post_gate", command="echo 2"))
        executor = RuntimeExecutor(auto, simulated=True)
        pre_results = executor.run_hooks(HookEvent.PRE_GATE, {})
        post_results = executor.run_hooks(HookEvent.POST_GATE, {})
        assert len(pre_results) == 1
        assert pre_results[0]["status"] == "simulated"
        assert len(post_results) == 1
        assert post_results[0]["status"] == "simulated"

    def test_simulated_mode_does_not_run_subprocess(self):
        auto = RuntimeAutomation()
        hook = RuntimeHook(
            event="lint_trigger",
            command="python -m py_compile {artifact}",
            required=False,
        )
        auto.register_hook(HookEvent.LINT_TRIGGER, hook)
        executor = RuntimeExecutor(auto, simulated=True)
        results = executor.run_hooks(HookEvent.LINT_TRIGGER, {"artifact": "/tmp/test.py"})
        assert len(results) == 1
        assert results[0]["status"] == "simulated"
        assert "return_code" not in results[0]

    def test_hook_command_with_placeholder_substitution(self):
        auto = RuntimeAutomation()
        hook = RuntimeHook(
            event="evaluation_trigger",
            command="pytest {test_path} --json-report",
            artifact_output="test-report.json",
            required=True,
        )
        auto.register_hook(HookEvent.EVALUATION_TRIGGER, hook)
        executor = RuntimeExecutor(auto, simulated=True)
        results = executor.run_hooks(
            HookEvent.EVALUATION_TRIGGER,
            {"test_path": "/workspace/test_suite.py"},
        )
        assert len(results) == 1
        assert results[0]["command"] == "pytest /workspace/test_suite.py --json-report"

    def test_required_hook_flag(self):
        auto = RuntimeAutomation()
        hook_required = RuntimeHook(event="pre_gate", command="echo required", required=True)
        hook_optional = RuntimeHook(event="pre_gate", command="echo optional", required=False)
        auto.register_hook(HookEvent.PRE_GATE, hook_required)
        auto.register_hook(HookEvent.PRE_GATE, hook_optional)
        executor = RuntimeExecutor(auto, simulated=True)
        results = executor.run_hooks(HookEvent.PRE_GATE, {})
        assert len(results) == 2
        for r in results:
            assert r["status"] == "simulated"

    def test_real_mode_success_hook_returns_success(self, monkeypatch):
        auto = RuntimeAutomation()
        auto.register_hook(HookEvent.LINT_TRIGGER, RuntimeHook(event="lint_trigger", command="pytest {artifact}"))
        executor = RuntimeExecutor(auto, simulated=False)

        def fake_run(cmd, *args, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, stdout="OK\n", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        results = executor.run_hooks(HookEvent.LINT_TRIGGER, {"artifact": "/tmp/test_suite.py"})
        assert len(results) == 1
        assert results[0]["status"] == "success"
        assert results[0]["return_code"] == 0

    def test_real_mode_failure_hook_returns_failed(self, monkeypatch):
        auto = RuntimeAutomation()
        auto.register_hook(HookEvent.LINT_TRIGGER, RuntimeHook(event="lint_trigger", command="pytest {artifact}"))
        executor = RuntimeExecutor(auto, simulated=False)

        def fake_run(cmd, *args, **kwargs):
            return subprocess.CompletedProcess(cmd, 2, stdout="", stderr="failed\n")

        monkeypatch.setattr(subprocess, "run", fake_run)
        results = executor.run_hooks(HookEvent.LINT_TRIGGER, {"artifact": "/tmp/test_suite.py"})
        assert len(results) == 1
        assert results[0]["status"] == "failed"
        assert results[0]["return_code"] == 2
        assert results[0]["stderr"] == "failed\n"

    def test_real_mode_timeout_is_reported(self, monkeypatch):
        auto = RuntimeAutomation()
        hook = RuntimeHook(event="lint_trigger", command="pytest {artifact}", timeout_seconds=2)
        auto.register_hook(HookEvent.LINT_TRIGGER, hook)
        executor = RuntimeExecutor(auto, simulated=False)

        def fake_run(cmd, *args, **kwargs):
            raise subprocess.TimeoutExpired(cmd, hook.timeout_seconds)

        monkeypatch.setattr(subprocess, "run", fake_run)
        results = executor.run_hooks(HookEvent.LINT_TRIGGER, {"artifact": "/tmp/test_suite.py"})
        assert len(results) == 1
        assert results[0]["status"] == "timeout"
        assert "excedeu timeout de 2s" in results[0]["reason"]

    def test_real_mode_error_is_reported(self, monkeypatch):
        auto = RuntimeAutomation()
        auto.register_hook(HookEvent.LINT_TRIGGER, RuntimeHook(event="lint_trigger", command="pytest {artifact}"))
        executor = RuntimeExecutor(auto, simulated=False)

        def fake_run(cmd, *args, **kwargs):
            raise RuntimeError("falha controlada")

        monkeypatch.setattr(subprocess, "run", fake_run)
        results = executor.run_hooks(HookEvent.LINT_TRIGGER, {"artifact": "/tmp/test_suite.py"})
        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert results[0]["reason"] == "falha controlada"


class TestExternalExecutorContracts:
    def test_registry_persistence(self, tmp_path: Path):
        registry = ExternalExecutorRegistry()
        registry.register(
            ExternalExecutorAdapter(
                name="codex-cli",
                transport="cli",
                entrypoint="codex exec --workspace {workspace} --sprint {sprint_id}",
                capabilities=["code", "tests"],
            )
        )
        path = tmp_path / "executors.json"
        save_executor_registry(registry, path)
        loaded = load_executor_registry(path)
        assert loaded.get("codex-cli").transport == "cli"
        assert loaded.get("codex-cli").capabilities == ["code", "tests"]

    def test_default_executor_registry_exposes_provider_aware_adapters(self):
        registry = create_default_executor_registry()
        names = {adapter.name for adapter in registry.list()}
        assert {'manual-review', 'local-cli', 'github-actions-review', 'gitlab-ci-review'} <= names
        assert registry.get('github-actions-review').required_context == ['repository', 'ci_run_id']
        assert registry.get('gitlab-ci-review').provider == 'gitlab-ci'

    def test_plan_external_dispatch_preserves_separation(self):
        registry = ExternalExecutorRegistry()
        registry.register(
            ExternalExecutorAdapter(
                name="manual-review",
                transport="manual",
                entrypoint="manual://handoff/{run_id}/{sprint_id}",
                requires_human_approval=True,
            )
        )
        bridge = ExternalExecutorBridge(registry)
        request = ExecutionDispatchRequest(
            run_id="run-1",
            sprint_id="SPRINT-1",
            demand="criar auth",
            objective="implementar login",
            workspace="/tmp/project",
            changed_files=["src/auth/login.py"],
        )
        result = bridge.plan("manual-review", request)
        assert result.status == "manual_required"
        assert "run-1" in result.planned_command

    def test_dispatch_cli_adapter_when_explicit(self, monkeypatch):
        registry = ExternalExecutorRegistry()
        registry.register(
            ExternalExecutorAdapter(
                name="local-cli",
                transport="cli",
                entrypoint="echo dispatch {run_id} {sprint_id}",
                requires_human_approval=False,
            )
        )
        bridge = ExternalExecutorBridge(registry)
        request = ExecutionDispatchRequest(
            run_id="run-1",
            sprint_id="SPRINT-1",
            demand="criar auth",
            objective="implementar login",
            workspace="/tmp/project",
        )

        def fake_run(cmd, *args, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)
        result = bridge.dispatch("local-cli", request, execute=True)
        assert result.status == "dispatched"
        assert result.metadata["return_code"] == 0
