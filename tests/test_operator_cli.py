import json
from pathlib import Path

import pytest

from cvg_harness.auto_runtime.external_executor import ExternalExecutorAdapter, ExternalExecutorRegistry
from cvg_harness.cli.cli import build_parser, cmd_dispatch, cmd_inspect, cmd_metrics
from cvg_harness.contracts.artifact_contracts import validate_artifact
from cvg_harness.operator.service import OperatorService


def _seed_project(tmp_path: Path) -> None:
    (tmp_path / 'src' / 'auth').mkdir(parents=True)
    (tmp_path / 'src' / 'auth' / 'login.py').write_text('def login():\n    return True\n')


def test_operator_run_creates_canonical_workspace(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)

    record = service.start_run('criar módulo de permissões por setor')

    root = tmp_path / '.cvg-harness'
    run_workspace = Path(record['run_workspace'])
    assert root.exists()
    assert (root / 'runs').exists()
    assert (root / 'current-run.txt').exists()
    assert run_workspace.exists()
    assert (run_workspace / 'logs' / 'event-log.jsonl').exists()
    assert (run_workspace / 'artifacts').exists()
    assert (run_workspace / 'reports').exists()
    assert (run_workspace / 'logs').exists()
    assert (run_workspace / 'ledgers').exists()
    assert (run_workspace / 'artifacts' / 'classification.json').exists()
    assert (run_workspace / 'artifacts' / 'research-notes.json').exists()
    assert (run_workspace / 'artifacts' / 'prd.json').exists()
    assert (run_workspace / 'artifacts' / 'spec.json').exists()
    assert (run_workspace / 'artifacts' / 'sprint-plan.json').exists()
    assert record['operator_status'] == 'waiting_input'
    assert record['pending_human_action'] == 'approve_sprint'
    assert record['next_action'] == 'cvg approve'


def test_operator_status_pause_and_approve(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')

    status = service.status()
    assert status['current_phase'] == 'sprint'
    assert status['current_gate'] == 'GATE_5'

    paused = service.pause()
    assert paused['operator_status'] == 'paused'

    approved = service.approve()
    assert approved['operator_status'] == 'active'
    assert approved['pending_human_action'] == 'provide_execution_inputs'
    assert 'cvg continue' in approved['next_action']


def test_operator_dispatch_plan_explicit_handoff(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')
    service.approve()

    payload = service.plan_external_execution(executor='manual-review')

    plan_path = Path(record['run_workspace']) / 'artifacts' / 'external-dispatch-plan.json'
    assert plan_path.exists()
    plan = json.loads(plan_path.read_text())
    assert plan['adapter'] == 'manual-review'
    assert plan['status'] == 'manual_required'
    assert payload['plan']['adapter'] == 'manual-review'
    assert validate_artifact('external-dispatch-plan.json', plan) == []
    inspect_payload = service.inspect()
    assert inspect_payload['external_dispatch_plan']['adapter'] == 'manual-review'
    assert inspect_payload.get('known_adapters')
    assert any(event['event_type'] == 'external_executor_planned' for event in inspect_payload['timeline'])


def test_operator_dispatch_preserves_runtime_provider_context(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')

    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        context={
            'repository': 'openai/cvg-harness',
            'ci_run_id': '77',
            'ci_url': 'https://ci.example/runs/77',
        },
        simulated=True,
        ci_result_json=json.dumps({
            'status': 'success',
            'ci_ref': 'https://ci.example/runs/77',
            'evidence_refs': ['ci://logs/77'],
        }),
    )
    service.approve()

    payload = service.plan_external_execution(executor='manual-review')

    plan_path = Path(record['run_workspace']) / 'artifacts' / 'external-dispatch-plan.json'
    plan = json.loads(plan_path.read_text())
    assert plan['runtime_profile'] == 'github-actions'
    assert plan['runtime_provider'] == 'github-actions'
    assert plan['request_metadata']['runtime_profile'] == 'github-actions'
    assert plan['request_metadata']['runtime_provider'] == 'github-actions'
    assert payload['plan']['runtime_provider'] == 'github-actions'
    assert payload['plan']['runtime_profile'] == 'github-actions'

    inspect_payload = service.inspect()
    assert inspect_payload['external_dispatch_plan']['runtime_provider'] == 'github-actions'
    assert inspect_payload['external_dispatch_plan']['runtime_profile'] == 'github-actions'
    assert inspect_payload['causal']['external_execution']['runtime_profile'] == 'github-actions'
    assert inspect_payload['causal']['external_execution']['runtime_provider'] == 'github-actions'


def test_operator_continue_requires_approval(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')

    with pytest.raises(ValueError):
        service.continue_run()


def test_operator_continue_with_guard_then_evidence_completes_release(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.approve()

    first = service.continue_run(changed_files=['src/auth/login.py'])
    assert first['guard']['result'] in {'PASS', 'WAIVER'}
    assert first['run']['pending_human_action'] == 'provide_evidence'

    second = service.continue_run(
        changed_files=['src/auth/login.py'],
        evidence=[
            'implementação dos arquivos',
            'testes unitários',
            'logs de execução',
            'implementação do módulo auth',
            'testes do módulo auth',
        ],
    )
    assert second['evaluation']['result'] == 'PASSED'
    assert second['release']['decision'] == 'APPROVED'
    assert second['run']['operator_status'] == 'completed'


def test_operator_continue_accepts_structured_evidence_file(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')
    service.approve()

    evidence_file = tmp_path / 'evidence.json'
    evidence_file.write_text(json.dumps({
        'items': [
            {'kind': 'implementation', 'summary': 'implementação dos arquivos', 'ref': 'src/auth/login.py'},
            {'kind': 'test', 'summary': 'testes unitários', 'ref': 'tests/test_auth.py'},
            {'kind': 'log', 'summary': 'logs de execução', 'ref': 'logs/auth.log'},
            {'kind': 'implementation', 'summary': 'implementação do módulo auth', 'module': 'auth'},
            {'kind': 'test', 'summary': 'testes do módulo auth', 'module': 'auth'},
        ]
    }))

    result = service.continue_run(
        changed_files=['src/auth/login.py'],
        evidence_file=str(evidence_file),
    )
    manifest_path = Path(record['run_workspace']) / 'artifacts' / 'evidence-manifest.json'
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert len(manifest['items']) == 5
    assert result['evaluation']['result'] == 'PASSED'
    assert result['evaluation']['structured_evidence_count'] == 5

def test_operator_continue_uses_structured_evidence_even_without_legacy_phrases(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.approve()

    evidence_file = tmp_path / 'evidence-opaque.json'
    evidence_file.write_text(json.dumps({
        'items': [
            {'kind': 'implementation', 'summary': 'patchset auth #42', 'ref': 'src/auth/login.py', 'module': 'auth'},
            {'kind': 'test', 'summary': 'pytest auth subset', 'ref': 'tests/test_auth.py', 'module': 'auth'},
            {'kind': 'log', 'summary': 'trace id=abc', 'ref': 'logs/auth.log', 'module': 'auth'},
        ]
    }))

    result = service.continue_run(
        changed_files=['src/auth/login.py'],
        evidence_file=str(evidence_file),
    )
    assert result['evaluation']['result'] == 'PASSED'
    assert result['evaluation']['evidence_missing'] == []
    assert result['evaluation']['structured_evidence_count'] == 3
    assert result['release']['decision'] == 'APPROVED'


def test_operator_inspect_exposes_causal_context(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.approve()
    service.continue_run(changed_files=['src/auth/login.py'])
    service.continue_run(
        changed_files=['src/auth/login.py'],
        evidence=[
            'implementação dos arquivos',
            'testes unitários',
            'logs de execução',
            'implementação do módulo auth',
            'testes do módulo auth',
        ],
    )

    payload = service.inspect()
    assert 'timeline' in payload
    assert payload['causal']['decisions']['release'] == 'APPROVED'
    assert payload['causal']['evidence']['total_items'] == 5
    assert 'src/auth/login.py' in payload['causal']['changed_files']
    assert any(event['event_type'] == 'evidence_registered' for event in payload['timeline'])


def test_operator_runtime_hooks_simulated(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')

    payload = service.run_runtime_hooks(
        event='lint_trigger',
        context={'artifact': 'src/auth/login.py'},
        simulated=True,
    )

    runtime_path = Path(record['run_workspace']) / 'artifacts' / 'runtime-hooks.json'
    assert runtime_path.exists()
    runtime = json.loads(runtime_path.read_text())
    assert runtime['event'] == 'lint_trigger'
    assert runtime['simulated'] is True
    assert runtime['profile'] == 'default'
    assert runtime['provider'] == 'generic'
    assert validate_artifact('runtime-hooks.json', runtime) == []
    assert runtime['external_evidence_refs'] == ['lint-output.json']
    assert payload['runtime_hooks']['results'][0]['status'] == 'simulated'

    external_path = Path(record['run_workspace']) / 'artifacts' / 'external-evidence-manifest.json'
    assert external_path.exists()
    external = json.loads(external_path.read_text())
    assert external['evidence_refs'] == ['lint-output.json']
    assert validate_artifact('external-evidence-manifest.json', external) == []

    inspect_payload = service.inspect()
    assert inspect_payload['runtime_hooks']['event'] == 'lint_trigger'
    assert inspect_payload['runtime_hooks']['profile'] == 'default'
    assert inspect_payload['runtime_hooks']['provider'] == 'generic'
    assert inspect_payload['external_evidence']['count'] == 1
    assert any(event['event_type'] == 'runtime_hooks_executed' for event in inspect_payload['timeline'])
    assert any(event['event_type'] == 'external_evidence_registered' for event in inspect_payload['timeline'])


def test_operator_ci_result_runtime_creates_canonical_ci_manifest(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')

    payload = service.run_runtime_hooks(
        event='ci_result',
        context={
            'ci_url': 'https://ci.example/runs/42',
            'ci_status': 'passed',
        },
        simulated=True,
        profile='ci-readonly',
    )

    ci_path = Path(record['run_workspace']) / 'artifacts' / 'ci-result.json'
    assert ci_path.exists()
    ci = json.loads(ci_path.read_text())
    assert ci['event'] == 'ci_result'
    assert ci['simulated'] is True
    assert ci['context']['ci_url'] == 'https://ci.example/runs/42'
    assert ci['status'] == 'passed'
    assert ci['ci_ref'] == 'https://ci.example/runs/42'
    assert ci['provider'] == 'generic-ci'
    assert validate_artifact('ci-result.json', ci) == []
    assert payload['ci_result']['ci_ref'] == 'https://ci.example/runs/42'
    assert payload['ci_result']['status'] == 'passed'

    inspect_payload = service.inspect()
    assert inspect_payload['ci_result']['present'] is True
    assert inspect_payload['ci_result']['status'] == 'passed'
    assert inspect_payload['ci_result']['ci_ref'] == 'https://ci.example/runs/42'
    assert inspect_payload['causal']['runtime']['profile_details']['provider'] == 'generic-ci'
    assert inspect_payload['causal']['runtime']['profile'] == 'ci-readonly'
    assert any(event['event_type'] == 'ci_result_registered' for event in inspect_payload['timeline'])


def test_operator_runtime_profiles_list_known_profiles(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    profiles = service.list_runtime_profiles()
    names = {profile['name'] for profile in profiles}
    assert {'default', 'ci-readonly', 'quality-gates', 'github-actions', 'gitlab-ci', 'azure-pipelines'} <= names
    gh_profile = next(profile for profile in profiles if profile['name'] == 'github-actions')
    assert gh_profile['provider'] == 'github-actions'
    assert gh_profile['command_examples']
    assert gh_profile['required_context']['ci_result'] == ['ci_run_id', 'repository']
    assert gh_profile['example_contexts']['ci_result'][0]['repository'] == 'openai/cvg-harness'
    az_profile = next(profile for profile in profiles if profile['name'] == 'azure-pipelines')
    assert az_profile['provider'] == 'azure-pipelines'
    assert az_profile['required_context']['ci_result'] == ['organization', 'project', 'build_id']


def test_operator_runtime_github_actions_profile_resolves_context_from_ci_result(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')

    payload = service.run_runtime_hooks(
        event='ci_result',
        context={},
        simulated=True,
        profile='github-actions',
        ci_result={
            'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42',
            'metadata': {'workflow': 'tests'},
        },
    )

    runtime = payload['runtime_hooks']
    assert runtime['context']['repository'] == 'openai/cvg-harness'
    assert runtime['context']['ci_run_id'] == '42'
    assert runtime['missing_required_context'] == []
    assert runtime['provider'] == 'github-actions'
    assert runtime['results'][0]['command'] == 'gh run view 42 --repo openai/cvg-harness --json conclusion,url,workflowName'

    ci_path = Path(record['run_workspace']) / 'artifacts' / 'ci-result.json'
    ci = json.loads(ci_path.read_text())
    assert ci['context']['repository'] == 'openai/cvg-harness'
    assert ci['context']['ci_run_id'] == '42'


def test_operator_runtime_azure_pipelines_profile_resolves_context_from_ci_result(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')

    payload = service.run_runtime_hooks(
        event='ci_result',
        context={},
        simulated=True,
        profile='azure-pipelines',
        ci_result={
            'ci_ref': 'https://dev.azure.com/openai/cvg-harness/_build/results?buildId=42',
        },
    )

    runtime = payload['runtime_hooks']
    assert runtime['context']['organization'] == 'openai'
    assert runtime['context']['project'] == 'cvg-harness'
    assert runtime['context']['build_id'] == '42'
    assert runtime['missing_required_context'] == []
    assert runtime['results'][0]['command'] == 'az pipelines runs show --id 42 --org openai --project cvg-harness'

    ci_path = Path(record['run_workspace']) / 'artifacts' / 'ci-result.json'
    ci = json.loads(ci_path.read_text())
    assert ci['context']['organization'] == 'openai'
    assert ci['context']['project'] == 'cvg-harness'
    assert ci['provider'] == 'azure-pipelines'


def test_operator_runtime_profile_rejects_unsupported_event(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')

    with pytest.raises(ValueError):
        service.run_runtime_hooks(event='lint_trigger', profile='ci-readonly', simulated=True)



def test_operator_runtime_persists_missing_context_hints_for_simulated_ci(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')

    payload = service.run_runtime_hooks(event='ci_result', profile='ci-readonly', simulated=True)

    runtime_path = Path(record['run_workspace']) / 'artifacts' / 'runtime-hooks.json'
    runtime = json.loads(runtime_path.read_text())
    assert runtime['missing_context_hints'] == ['ci_result_url', 'ci_result_file', 'ci_result_json']
    assert payload['runtime_hooks']['missing_context_hints'] == ['ci_result_url', 'ci_result_file', 'ci_result_json']
    inspect_payload = service.inspect()
    assert inspect_payload['causal']['runtime']['missing_context_hints'] == ['ci_result_url', 'ci_result_file', 'ci_result_json']



def test_operator_runtime_real_requires_minimum_context(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')

    with pytest.raises(ValueError):
        service.run_runtime_hooks(event='ci_result', profile='ci-readonly', simulated=False)


def test_operator_github_actions_profile_derives_runtime_context_from_github_url(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')

    ci_file = tmp_path / 'gha-ci-result.json'
    ci_file.write_text(json.dumps({
        'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42',
        'status': 'passed',
        'metadata': {'workflow': 'tests'},
    }))

    payload = service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        ci_result_file=str(ci_file),
        simulated=True,
    )

    runtime = payload['runtime_hooks']
    ci = payload['ci_result']
    assert runtime['resolved_context']['repository'] == 'openai/cvg-harness'
    assert runtime['resolved_context']['ci_run_id'] == '42'
    assert runtime['resolved_context']['ci_api'] == 'https://api.github.com/repos/openai/cvg-harness/actions/runs/42'
    assert 'gh run view 42 --repo openai/cvg-harness' in runtime['results'][0]['command']
    assert runtime['required_context'] == ['ci_run_id', 'repository']
    assert runtime['missing_required_context'] == []
    assert ci['context']['repository'] == 'openai/cvg-harness'
    assert ci['context']['ci_run_id'] == '42'
    assert ci['context']['ci_api'] == 'https://api.github.com/repos/openai/cvg-harness/actions/runs/42'
    inspect_payload = service.inspect()
    assert inspect_payload['causal']['runtime']['profile'] == 'github-actions'
    assert inspect_payload['causal']['runtime']['required_context'] == ['ci_run_id', 'repository']



def test_operator_gitlab_profile_preserves_ci_api_context(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')

    payload = service.run_runtime_hooks(
        event='ci_result',
        profile='gitlab-ci',
        context={'ci_api': 'https://gitlab.example/api/v4/projects/123/jobs/456'},
        simulated=True,
    )

    runtime = payload['runtime_hooks']
    assert runtime['resolved_context']['ci_api'] == 'https://gitlab.example/api/v4/projects/123/jobs/456'
    assert runtime['resolved_context']['ci_result_url'] == 'https://gitlab.example/api/v4/projects/123/jobs/456'
    assert 'curl -s https://gitlab.example/api/v4/projects/123/jobs/456' in runtime['results'][0]['command']
    assert runtime['required_context'] == ['ci_api']
    assert runtime['missing_required_context'] == []


def test_operator_ci_result_runtime_accepts_external_json_file(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')

    ci_file = tmp_path / 'ci-result.json'
    ci_file.write_text(json.dumps({
        'ci_ref': 'https://ci.example/runs/99',
        'status': 'failed',
        'evidence_refs': ['reports/ci.log', 'reports/tests.xml'],
        'metadata': {'branch': 'main'},
    }))

    payload = service.run_runtime_hooks(
        event='ci_result',
        ci_result_file=str(ci_file),
        simulated=True,
    )

    ci_path = Path(record['run_workspace']) / 'artifacts' / 'ci-result.json'
    ci = json.loads(ci_path.read_text())
    assert ci['ci_ref'] == 'https://ci.example/runs/99'
    assert ci['status'] == 'failed'
    assert sorted(ci['evidence_refs']) == ['ci-result.json', 'reports/ci.log', 'reports/tests.xml']
    assert ci['metadata']['branch'] == 'main'
    assert payload['ci_result']['source'] == 'external_ci'
    assert payload['runtime_hooks']['results'][0]['command'] == f"curl -s {ci_file.resolve().as_uri()}"
    inspect_payload = service.inspect()
    assert inspect_payload['ci_result']['ci_ref'] == 'https://ci.example/runs/99'


def test_operator_ci_result_runtime_accepts_external_json_url(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')

    ci_file = tmp_path / 'remote-ci-result.json'
    ci_file.write_text(json.dumps({
        'ci_ref': 'https://ci.example/runs/101',
        'status': 'passed',
        'evidence_refs': ['reports/ci.log'],
        'metadata': {'branch': 'release'},
    }))

    payload = service.run_runtime_hooks(
        event='ci_result',
        ci_result_url=ci_file.as_uri(),
        simulated=True,
    )

    ci_path = Path(record['run_workspace']) / 'artifacts' / 'ci-result.json'
    ci = json.loads(ci_path.read_text())
    assert ci['ci_ref'] == 'https://ci.example/runs/101'
    assert ci['status'] == 'passed'
    assert payload['ci_result']['ci_ref'] == 'https://ci.example/runs/101'
    assert payload['ci_result']['source'] == 'external_ci'
    assert payload['runtime_hooks']['results'][0]['command'] == f"curl -s {ci_file.as_uri()}"


def test_cli_inspect_prints_runtime_summary(tmp_path: Path, capsys):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.run_runtime_hooks(
        event='lint_trigger',
        context={'artifact': 'src/auth/login.py'},
        simulated=True,
    )

    class Args:
        workspace = str(tmp_path)
        json = False
        target = None

    cmd_inspect(Args())
    out = capsys.readouterr().out
    assert 'Runtime:' in out
    assert 'lint_trigger' in out
    assert 'profile_details' in out
    assert 'provider' in out


def test_cli_runtime_profiles_print_known_profiles(tmp_path: Path, capsys):
    _seed_project(tmp_path)
    class Args:
        workspace = str(tmp_path)
        json = False

    from cvg_harness.cli.cli import cmd_runtime_profiles

    cmd_runtime_profiles(Args())
    out = capsys.readouterr().out
    assert 'default' in out
    assert 'ci-readonly' in out
    assert 'context_hints' in out
    assert 'required_context' in out
    assert 'example_contexts' in out
    assert 'provider' in out


def test_cli_help_prioritizes_operator_commands():
    parser = build_parser()
    help_text = parser.format_help()
    assert help_text.index('run') < help_text.index('classify')
    assert '[operator]' in help_text
    assert '[advanced]' in help_text
    assert 'adapters' in help_text
    assert 'runtime-profiles' in help_text
    choices = next(action for action in parser._actions if getattr(action, 'choices', None)).choices
    continue_help = choices['continue'].format_help()
    assert '--evidence-file' in continue_help
    assert '--evidence-json' in continue_help
    dispatch_help = choices['dispatch'].format_help()
    assert '--executor' in dispatch_help
    assert '--capability' in dispatch_help
    assert '--context-json' in dispatch_help
    assert '--repository' in dispatch_help
    assert '--ci-run-id' in dispatch_help
    adapters_help = choices['adapters'].format_help()
    assert '--json' in adapters_help
    assert '--capability' in adapters_help
    runtime_profiles_help = choices['runtime-profiles'].format_help()
    assert '--json' in runtime_profiles_help
    runtime_help = choices['runtime'].format_help()
    assert '--event' in runtime_help
    assert '--real' in runtime_help
    assert '--profile' in runtime_help
    assert '--repository' in runtime_help
    assert '--ci-run-id' in runtime_help
    assert '--ci-api' in runtime_help


def test_operator_registry_load_merges_new_default_adapters(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.executors_registry_file.write_text("""{
  "adapters": {
    "manual-review": {
      "name": "manual-review",
      "transport": "manual",
      "entrypoint": "manual://handoff/{run_id}/{sprint_id}",
      "capabilities": ["planning", "review"],
      "emits_evidence": true,
      "requires_human_approval": true,
      "description": "legacy"
    }
  }
}
""")

    adapters = service.list_adapters()
    names = {adapter['name'] for adapter in adapters}
    assert 'manual-review' in names
    assert 'github-actions-review' in names
    assert 'gitlab-ci-review' in names


def test_operator_adapters_lists_known_adapters(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    adapters = service.list_adapters()

    names = {adapter['name'] for adapter in adapters}
    assert {'manual-review', 'local-cli', 'github-actions-review', 'gitlab-ci-review'} <= names
    gha = next(adapter for adapter in adapters if adapter['name'] == 'github-actions-review')
    assert gha['provider'] == 'github-actions'
    assert gha['required_context'] == ['repository', 'ci_run_id']


def test_operator_adapters_rank_by_capability_and_provider_context(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42'},
    )

    adapters = service.list_adapters(capability='ci')
    assert adapters[0]['name'] == 'github-actions-review'
    assert adapters[0]['suitability_score'] > adapters[1]['suitability_score']
    assert 'provider:github-actions' in adapters[0]['selection_reason']


def test_operator_adapters_apply_review_policy_prefer_manual(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42'},
    )

    adapters = service.list_adapters(capability='review')
    assert adapters[0]['name'] == 'manual-review'
    assert 'policy:prefer_manual' in adapters[0]['selection_reason']


def test_operator_adapters_apply_project_policy_override(tmp_path: Path):
    _seed_project(tmp_path)
    root = tmp_path / '.cvg-harness'
    root.mkdir(exist_ok=True)
    (root / 'adapter-policy.json').write_text(json.dumps({
        'capabilities': {
            'ci': {
                'preferred_adapters': ['gitlab-ci-review'],
                'disabled_adapters': ['github-actions-review'],
            }
        }
    }, indent=2))

    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42'},
    )

    adapters = service.list_adapters(capability='ci')
    assert adapters[0]['name'] == 'gitlab-ci-review'
    assert adapters[0]['policy_source'] == 'default+project'
    assert 'policy_adapter:gitlab-ci-review' in adapters[0]['selection_reason']
    assert all(adapter['name'] != 'github-actions-review' for adapter in adapters)


def test_cli_adapters_print_provider_details(tmp_path: Path, capsys):
    _seed_project(tmp_path)

    class Args:
        workspace = str(tmp_path)
        json = False
        capability = 'ci'
        repository = None
        ci_run_id = None
        ci_api = None
        ci_url = None
        ci_status = None
        context_json = None

    from cvg_harness.cli.cli import cmd_adapters

    cmd_adapters(Args())
    out = capsys.readouterr().out
    assert 'github-actions-review' in out
    assert 'provider: github-actions' in out
    assert 'required_context:' in out
    assert 'command_examples:' in out
    assert 'policy_source:' in out


def test_operator_dispatch_selects_adapter_by_capability(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.approve()
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42'},
    )

    payload = service.plan_external_execution(capability='ci')
    assert payload['plan']['adapter'] == 'github-actions-review'
    assert payload['plan']['capability'] == 'ci'
    assert 'capability:ci' in payload['plan']['selection_reason']
    assert payload['plan']['alternative_adapters']
    assert payload['plan']['alternative_adapters'][0]['name'] in {'gitlab-ci-review', 'manual-review'}


def test_cli_dispatch_accepts_capability_selection(tmp_path: Path, capsys):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.approve()
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42'},
    )

    class Args:
        executor = None
        capability = 'ci'
        workspace = str(tmp_path)
        execute = False
        json = False
        context_json = None
        repository = None
        ci_run_id = None
        ci_api = None
        ci_url = None
        ci_status = None

    cmd_dispatch(Args())
    out = capsys.readouterr().out
    assert 'Executor: github-actions-review' in out
    assert 'Capability: ci' in out
    assert 'Selection reason:' in out
    assert 'Policy source:' in out
    assert 'Active policy:' in out
    assert 'Alternative adapters:' in out


def test_operator_dispatch_selects_manual_review_by_review_policy(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.approve()
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42'},
    )

    payload = service.plan_external_execution(capability='review')
    assert payload['plan']['adapter'] == 'manual-review'
    assert 'policy:prefer_manual' in payload['plan']['selection_reason']
    assert payload['plan']['alternative_adapters']
    assert payload['plan']['alternative_adapters'][0]['name'] == 'github-actions-review'


def test_operator_dispatch_persists_project_policy_metadata(tmp_path: Path):
    _seed_project(tmp_path)
    root = tmp_path / '.cvg-harness'
    root.mkdir(exist_ok=True)
    (root / 'adapter-policy.json').write_text(json.dumps({
        'capabilities': {
            'review': {
                'preferred_adapters': ['github-actions-review'],
                'prefer_manual': False,
                'disabled_adapters': ['manual-review'],
            }
        }
    }, indent=2))

    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.approve()
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42'},
    )

    payload = service.plan_external_execution(capability='review')
    assert payload['plan']['adapter'] == 'github-actions-review'
    assert payload['plan']['policy_source'] == 'default+project'
    assert payload['plan']['active_policy']['disabled_adapters'] == ['manual-review']
    assert 'policy_adapter:github-actions-review' in payload['plan']['selection_reason']
    assert all(item['name'] != 'manual-review' for item in payload['plan']['alternative_adapters'])


def test_operator_dispatch_executes_provider_aware_cli_adapter(tmp_path: Path, monkeypatch):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.approve()
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42'},
    )

    from cvg_harness.auto_runtime import external_executor as external_executor_module

    def fake_run(cmd, *args, **kwargs):
        return __import__('subprocess').CompletedProcess(cmd, 0, stdout='ok', stderr='')

    monkeypatch.setattr(external_executor_module.subprocess, 'run', fake_run)
    payload = service.plan_external_execution(executor='github-actions-review', execute=True)

    assert payload['plan']['status'] == 'dispatched'
    assert 'gh run view 42 --repo openai/cvg-harness' in payload['plan']['planned_command']


def test_cli_runtime_accepts_provider_context_shortcuts(tmp_path: Path, capsys):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')

    class Args:
        workspace = str(tmp_path)
        json = False
        event = 'ci_result'
        context_json = None
        repository = 'openai/cvg-harness'
        ci_run_id = '77'
        ci_api = None
        ci_url = None
        ci_status = 'passed'
        profile = 'github-actions'
        ci_result_json = None
        ci_result_file = None
        ci_result_url = None
        real = False

    from cvg_harness.cli.cli import cmd_runtime

    cmd_runtime(Args())
    out = capsys.readouterr().out
    assert 'Provider: github-actions' in out
    assert 'Available context keys:' in out

    inspect_payload = service.inspect()
    runtime = inspect_payload['runtime_hooks']
    assert runtime['context']['repository'] == 'openai/cvg-harness'
    assert runtime['context']['ci_run_id'] == '77'
    assert runtime['context']['ci_status'] == 'passed'
    assert runtime['missing_required_context'] == []


def test_cli_metrics_prints_runtime_provider_breakdown(tmp_path: Path, capsys):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={
            'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42',
            'metadata': {'workflow': 'tests'},
        },
    )

    class Args:
        workspace = str(tmp_path)
        json = False

    cmd_metrics(Args())
    out = capsys.readouterr().out
    assert 'Runtime providers:' in out
    assert 'github-actions' in out


def test_operator_dispatch_derives_context_from_runtime_ci(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')
    service.approve()
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        simulated=True,
        ci_result={
            'ci_ref': 'https://github.com/openai/cvg-harness/actions/runs/42',
            'metadata': {'workflow': 'tests'},
        },
    )

    payload = service.plan_external_execution(executor='manual-review')

    plan_path = Path(record['run_workspace']) / 'artifacts' / 'external-dispatch-plan.json'
    plan = json.loads(plan_path.read_text())
    assert plan['provider'] == 'human-review'
    assert validate_artifact('external-dispatch-plan.json', plan) == []
    assert plan['context']['repository'] == 'openai/cvg-harness'
    assert plan['context']['ci_run_id'] == '42'
    assert plan['context']['ci_ref'] == 'https://github.com/openai/cvg-harness/actions/runs/42'
    assert 'runtime_hooks' in plan['context_sources']
    assert 'ci_result' in plan['context_sources']
    assert payload['plan']['available_context_keys']

    inspect_payload = service.inspect()
    assert inspect_payload['causal']['external_execution']['provider'] == 'human-review'
    assert 'repository' in inspect_payload['causal']['external_execution']['available_context_keys']


def test_operator_dispatch_execute_requires_required_context(tmp_path: Path, monkeypatch):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.approve()

    registry = ExternalExecutorRegistry()
    registry.register(
        ExternalExecutorAdapter(
            name='provider-cli',
            transport='cli',
            entrypoint='echo dispatch {repository} {ci_run_id}',
            requires_human_approval=False,
            provider='github-actions',
            required_context=['repository', 'ci_run_id'],
        )
    )
    monkeypatch.setattr(service, '_load_executor_registry', lambda: registry)

    with pytest.raises(ValueError):
        service.plan_external_execution(executor='provider-cli', execute=True)


def test_cli_dispatch_accepts_provider_context_shortcuts(tmp_path: Path, capsys):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        context={
            'repository': 'openai/cvg-harness',
            'ci_run_id': '91',
            'ci_url': 'https://ci.example/runs/91',
        },
        simulated=True,
        ci_result_json=json.dumps({
            'status': 'success',
            'ci_ref': 'https://ci.example/runs/91',
            'evidence_refs': ['ci://logs/91'],
        }),
    )
    service.approve()

    class Args:
        executor = 'manual-review'
        workspace = str(tmp_path)
        execute = False
        json = False
        context_json = None
        repository = 'openai/cvg-harness'
        ci_run_id = '91'
        ci_api = None
        ci_url = None
        ci_status = 'passed'

    cmd_dispatch(Args())
    out = capsys.readouterr().out
    assert 'Provider: human-review' in out
    assert 'Runtime provider: github-actions' in out
    assert 'Available context keys:' in out

    inspect_payload = service.inspect()
    plan = inspect_payload['external_dispatch_plan']
    assert plan['context']['repository'] == 'openai/cvg-harness'
    assert plan['context']['ci_run_id'] == '91'
    assert 'runtime_hooks' in plan['context_sources']
    assert 'operator_input' in plan['context_sources']


def test_cli_inspect_prints_external_dispatch_summary(tmp_path: Path, capsys):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    service.start_run('criar módulo de permissões por setor')
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        context={
            'repository': 'openai/cvg-harness',
            'ci_run_id': '94',
            'ci_url': 'https://ci.example/runs/94',
        },
        simulated=True,
        ci_result_json=json.dumps({
            'status': 'success',
            'ci_ref': 'https://ci.example/runs/94',
            'evidence_refs': ['ci://logs/94'],
        }),
    )
    service.approve()
    service.plan_external_execution(executor='local-cli', execute=True)

    class Args:
        workspace = str(tmp_path)
        json = False
        target = None

    cmd_inspect(Args())
    out = capsys.readouterr().out
    assert 'Execução externa: executor=local-cli' in out
    assert 'runtime_provider=github-actions' in out
    assert 'Plano: ' in out
    assert 'Resultado: ' in out


def test_operator_dispatch_executes_local_cli_and_records_result(tmp_path: Path):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        context={
            'repository': 'openai/cvg-harness',
            'ci_run_id': '92',
            'ci_url': 'https://ci.example/runs/92',
        },
        simulated=True,
        ci_result_json=json.dumps({
            'status': 'success',
            'ci_ref': 'https://ci.example/runs/92',
            'evidence_refs': ['ci://logs/92'],
        }),
    )
    service.approve()

    payload = service.plan_external_execution(executor='local-cli', execute=True)

    result_path = Path(record['run_workspace']) / 'reports' / 'external-dispatch-result.json'
    assert result_path.exists()
    result = json.loads(result_path.read_text())
    assert result['adapter'] == 'local-cli'
    assert result['runtime_profile'] == 'github-actions'
    assert result['runtime_provider'] == 'github-actions'
    assert 'runtime_hooks' in result['context_sources']
    assert result['request_metadata']['runtime_profile'] == 'github-actions'
    assert payload['plan']['status'] == 'dispatched'
    assert validate_artifact('external-dispatch-result.json', result) == []

    inspect_payload = service.inspect()
    assert inspect_payload['external_dispatch_result']['status'] == 'dispatched'
    assert inspect_payload['external_dispatch_result']['runtime_provider'] == 'github-actions'
    assert inspect_payload['causal']['external_execution']['runtime_provider'] == 'github-actions'
    assert inspect_payload['causal']['external_execution']['plan']['runtime_provider'] == 'github-actions'
    assert inspect_payload['causal']['external_execution']['result']['runtime_provider'] == 'github-actions'
    assert any(event['event_type'] == 'external_executor_dispatched' for event in inspect_payload['timeline'])


def test_operator_dispatch_records_failed_external_execution(tmp_path: Path, monkeypatch):
    _seed_project(tmp_path)
    service = OperatorService(tmp_path)
    record = service.start_run('criar módulo de permissões por setor')
    service.run_runtime_hooks(
        event='ci_result',
        profile='github-actions',
        context={
            'repository': 'openai/cvg-harness',
            'ci_run_id': '93',
            'ci_url': 'https://ci.example/runs/93',
        },
        simulated=True,
        ci_result_json=json.dumps({
            'status': 'success',
            'ci_ref': 'https://ci.example/runs/93',
            'evidence_refs': ['ci://logs/93'],
        }),
    )
    service.approve()

    from cvg_harness.auto_runtime import external_executor as external_executor_module

    def fake_run(cmd, *args, **kwargs):
        return __import__('subprocess').CompletedProcess(cmd, 1, stdout='', stderr='boom')

    monkeypatch.setattr(external_executor_module.subprocess, 'run', fake_run)

    payload = service.plan_external_execution(executor='local-cli', execute=True)

    result_path = Path(record['run_workspace']) / 'reports' / 'external-dispatch-result.json'
    assert result_path.exists()
    result = json.loads(result_path.read_text())
    assert result['status'] == 'failed'
    assert result['runtime_profile'] == 'github-actions'
    assert result['runtime_provider'] == 'github-actions'
    assert result['request_metadata']['runtime_provider'] == 'github-actions'
    assert payload['plan']['status'] == 'failed'
    assert validate_artifact('external-dispatch-result.json', result) == []

    inspect_payload = service.inspect()
    assert inspect_payload['external_dispatch_result']['status'] == 'failed'
    assert inspect_payload['external_dispatch_result']['runtime_provider'] == 'github-actions'
    assert inspect_payload['causal']['external_execution']['runtime_provider'] == 'github-actions'
    assert inspect_payload['causal']['external_execution']['plan']['runtime_provider'] == 'github-actions'
    assert inspect_payload['causal']['external_execution']['result']['runtime_provider'] == 'github-actions'
    assert any(event['event_type'] == 'external_execution_failed' for event in inspect_payload['timeline'])
