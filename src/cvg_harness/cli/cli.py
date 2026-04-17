"""
CLI para o CVG Harness.
Uso: cvg <comando> [opções]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cvg_harness.classification.classifier import classify, save_classification
from cvg_harness.contracts.handoff import create_handoff
from cvg_harness.drift.drift_detector import DriftDetector
from cvg_harness.guardian.architecture_guardian import ArchitectureGuardian
from cvg_harness.ledger.event_log import Event, EventLog
from cvg_harness.ledger.progress_ledger import ProgressLedger, load_progress, save_progress
from cvg_harness.linter.spec_linter import lint_spec, save_lint_report
from cvg_harness.operator.service import OperatorService
from cvg_harness.templates.revised_templates import render_prd, render_spec, render_sprint_plan


class CLIError(Exception):
    """Erro tratado da CLI."""
    pass


def _parse_json(value: str | None, label: str) -> dict:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise CLIError(f"{label} inválido: {exc}") from exc


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _build_runtime_context(args) -> dict:
    context_json = getattr(args, 'context_json', None)
    context = _parse_json(context_json, 'Contexto') if context_json else {}
    explicit = {
        'repository': getattr(args, 'repository', None),
        'ci_run_id': getattr(args, 'ci_run_id', None),
        'ci_api': getattr(args, 'ci_api', None),
        'ci_url': getattr(args, 'ci_url', None),
        'ci_status': getattr(args, 'ci_status', None),
    }
    context.update({key: value for key, value in explicit.items() if value})
    return context


def _service(args) -> OperatorService:
    return OperatorService(Path(args.workspace or Path.cwd()))


def cmd_run(args):
    record = _service(args).start_run(demand=args.demand, project=args.project, mode=args.mode)
    print(f"Run iniciada: {record['run_id']}")
    print(f"Projeto: {record['project']}")
    print(f"Modo: {record['mode']}")
    print(f"Workspace: {record['run_workspace']}")
    print(f"Fase: {record['current_phase']} | Gate: {record['current_gate']}")
    print(f"Próximo passo: {record['next_action']}")


def cmd_status(args):
    payload = _service(args).status()
    if args.json:
        _print_json(payload)
        return
    print(f"Projeto: {payload['project']}")
    print(f"Demanda: {payload['demand']}")
    print(f"Run: {payload['run_id']}")
    print(f"Modo: {payload['mode']}")
    print(f"Status operador: {payload['operator_status']}")
    print(f"Fase atual: {payload['current_phase']}")
    print(f"Gate atual: {payload['current_gate']}")
    print(f"Sprint atual: {payload['current_sprint'] or '-'}")
    print(f"Bloqueios: {payload['blockers'] or []}")
    print(f"Próximo passo: {payload['next_action']}")
    print(f"Resumo: {payload['summary']}")


def cmd_inspect(args):
    payload = _service(args).inspect(target=args.target)
    if args.json:
        _print_json(payload)
        return
    run = payload['run']
    print(f"Run: {run['run_id']} ({run['operator_status']})")
    print(f"Projeto: {run['project']}")
    print(f"Demanda: {run['demand']}")
    print(f"Fase/Gate: {run['current_phase']} / {run['current_gate']}")
    print(f"Pendência humana: {run['pending_human_action'] or '-'}")
    print(f"Artefatos: {payload.get('artifacts', [])}")
    print(f"Relatórios: {payload.get('reports', [])}")
    causal = payload.get('causal', {})
    if causal:
        print(f"Objetivo da sprint: {causal.get('objective') or '-'}")
        print(f"Changed files: {causal.get('changed_files') or []}")
        print(f"Evidências: {causal.get('evidence', {}).get('total_items', 0)} itens")
        print(f"Evidências faltantes: {causal.get('evidence', {}).get('missing', [])}")
        external_execution = causal.get('external_execution', {})
        if external_execution:
            print(
                "Execução externa: "
                f"executor={external_execution.get('executor', '-')}, "
                f"provider={external_execution.get('provider', '-')}, "
                f"runtime_provider={external_execution.get('runtime_provider', '-')}, "
                f"status={external_execution.get('status', '-')}"
            )
            plan = external_execution.get('plan', {})
            if plan:
                print(
                    "  Plano: "
                    f"provider={plan.get('provider', '-')}, "
                    f"runtime_provider={plan.get('runtime_provider', '-')}, "
                    f"status={plan.get('status', '-')}"
                )
            result = external_execution.get('result', {})
            if result:
                print(
                    "  Resultado: "
                    f"provider={result.get('provider', '-')}, "
                    f"runtime_provider={result.get('runtime_provider', '-')}, "
                    f"status={result.get('status', '-')}"
                )
        if causal.get('external_evidence', {}).get('present'):
            print(f"Evidência externa: {causal.get('external_evidence', {})}")
        if causal.get('ci_result', {}).get('present'):
            print(f"CI result: {causal.get('ci_result', {})}")
        if causal.get('runtime', {}).get('executed'):
            print(f"Runtime: {causal.get('runtime', {})}")
            profile_details = causal.get('runtime', {}).get('profile_details', {})
            if profile_details:
                print(f"Runtime profile: {causal.get('runtime', {}).get('profile', 'default')} [{profile_details.get('provider', '-')}]")
                if profile_details.get('command_examples'):
                    print(f"  command_examples: {profile_details.get('command_examples', [])}")
                if profile_details.get('context_hints'):
                    print(f"  profile_context_hints: {profile_details.get('context_hints', {})}")
        print(f"Decisões: {causal.get('decisions', {})}")
        print(f"Blockers: {causal.get('blockers', [])}")
    if payload.get('sprint'):
        print('Sprint:')
        _print_json(payload['sprint'])
    elif payload.get('sprints'):
        print('Sprints:')
        for sprint in payload['sprints']:
            print(f"  - {sprint.get('sprint_id')}: {sprint.get('objetivo', sprint.get('goal', 'sem objetivo'))}")
    if payload.get('evaluation'):
        print(f"Evaluation: {payload['evaluation'].get('result')}")


def cmd_continue(args):
    payload = _service(args).continue_run(
        changed_files=args.changed_file or [],
        evidence=args.evidence or [],
        evidence_json=args.evidence_json,
        evidence_file=args.evidence_file,
        round_num=args.round,
    )
    if args.json:
        _print_json(payload)
        return
    run = payload['run']
    print(f"Run: {run['run_id']}")
    if payload.get('guard'):
        print(f"Guard: {payload['guard']['result']}")
    if payload.get('evidence_manifest'):
        print(f"Evidence items: {len(payload['evidence_manifest'].get('items', []))}")
    if payload.get('evaluation'):
        print(f"Evaluation: {payload['evaluation']['result']}")
    if payload.get('drift'):
        print(f"Drift: {payload['drift']['result']}")
    if payload.get('release'):
        print(f"Release: {payload['release']['decision']}")
    print(f"Status operador: {run['operator_status']}")
    print(f"Próximo passo: {run['next_action']}")
    print(f"Resumo: {run['summary']}")


def cmd_pause(args):
    payload = _service(args).pause()
    print(f"Run pausada: {payload['run_id']}")
    print(f"Próximo passo: {payload['next_action']}")


def cmd_approve(args):
    payload = _service(args).approve(sprint_id=args.target)
    print(f"Sprint aprovada para execução controlada: {payload['current_sprint'] or '-'}")
    print(f"Próximo passo: {payload['next_action']}")


def cmd_dispatch(args):
    payload = _service(args).plan_external_execution(
        executor=args.executor,
        capability=getattr(args, 'capability', None),
        execute=args.execute,
        context=_build_runtime_context(args),
    )
    if args.json:
        _print_json(payload)
        return
    print(f"Executor: {payload['plan']['adapter']}")
    if payload['plan'].get('capability'):
        print(f"Capability: {payload['plan'].get('capability')}")
    if payload['plan'].get('selection_reason'):
        print(f"Selection reason: {payload['plan'].get('selection_reason', [])}")
    if payload['plan'].get('policy_source'):
        print(f"Policy source: {payload['plan'].get('policy_source')}")
    if payload['plan'].get('active_policy'):
        print(f"Active policy: {payload['plan'].get('active_policy', {})}")
    print(f"Provider: {payload['plan'].get('provider', '-')}")
    if payload['plan'].get('runtime_profile'):
        print(f"Runtime profile: {payload['plan'].get('runtime_profile', '-')}")
    if payload['plan'].get('runtime_provider'):
        print(f"Runtime provider: {payload['plan'].get('runtime_provider', '-')}")
    print(f"Status: {payload['plan']['status']}")
    print(f"Comando planejado: {payload['plan']['planned_command']}")
    if payload['plan'].get('context_sources'):
        print(f"Context sources: {payload['plan'].get('context_sources', [])}")
    if payload['plan'].get('required_context'):
        print(f"Required context: {payload['plan'].get('required_context', [])}")
    if payload['plan'].get('missing_required_context'):
        print(f"Missing required context: {payload['plan'].get('missing_required_context', [])}")
    if payload['plan'].get('available_context_keys'):
        print(f"Available context keys: {payload['plan'].get('available_context_keys', [])}")
    if payload['plan'].get('alternative_adapters'):
        print(f"Alternative adapters: {payload['plan'].get('alternative_adapters', [])}")
    print(f"Próximo passo: {payload['run']['next_action']}")


def cmd_adapters(args):
    payload = _service(args).list_adapters(capability=getattr(args, 'capability', None), context=_build_runtime_context(args))
    if args.json:
        _print_json(payload)
        return
    for adapter in payload:
        print(f"{adapter['name']} [{adapter['transport']}] - {adapter.get('description') or 'sem descrição'}")
        if adapter.get('provider'):
            print(f"  provider: {adapter.get('provider')}")
        print(f"  capabilities: {adapter.get('capabilities', [])}")
        if adapter.get('required_context'):
            print(f"  required_context: {adapter.get('required_context', [])}")
        if adapter.get('context_hints'):
            print(f"  context_hints: {adapter.get('context_hints', [])}")
        if adapter.get('command_examples'):
            print(f"  command_examples: {adapter.get('command_examples', [])}")
        if 'suitability_score' in adapter:
            print(f"  suitability_score: {adapter.get('suitability_score')}")
        if adapter.get('selection_reason'):
            print(f"  selection_reason: {adapter.get('selection_reason', [])}")
        if adapter.get('policy_source'):
            print(f"  policy_source: {adapter.get('policy_source')}")
        if adapter.get('active_policy'):
            print(f"  active_policy: {adapter.get('active_policy', {})}")
        print(f"  requires_human_approval: {adapter.get('requires_human_approval', True)}")


def cmd_runtime_profiles(args):
    payload = _service(args).list_runtime_profiles()
    if args.json:
        _print_json(payload)
        return
    for profile in payload:
        print(f"{profile['name']} - {profile['description']}")
        if profile.get('provider'):
            print(f"  provider: {profile['provider']}")
        print(f"  events: {profile.get('events', [])}")
        if profile.get('required_context'):
            print(f"  required_context: {profile.get('required_context', {})}")
        if profile.get('example_contexts'):
            print(f"  example_contexts: {profile.get('example_contexts', {})}")
        if profile.get('command_examples'):
            print(f"  command_examples: {profile.get('command_examples', [])}")
        if profile.get('context_hints'):
            print(f"  context_hints: {profile.get('context_hints', {})}")


def cmd_runtime(args):
    payload = _service(args).run_runtime_hooks(
        event=args.event,
        context=_build_runtime_context(args),
        simulated=not args.real,
        profile=args.profile,
        ci_result=_parse_json(args.ci_result_json, 'CI result') if args.ci_result_json else None,
        ci_result_json=args.ci_result_json,
        ci_result_file=args.ci_result_file,
        ci_result_url=args.ci_result_url,
    )
    if args.json:
        _print_json(payload)
        return
    runtime_hooks = payload['runtime_hooks']
    print(f"Runtime event: {runtime_hooks['event']}")
    print(f"Profile: {runtime_hooks.get('profile', 'default')}")
    print(f"Provider: {runtime_hooks.get('provider', '-')}")
    print(f"Simulated: {runtime_hooks['simulated']}")
    if runtime_hooks.get('context_hints'):
        print(f"Context hints: {runtime_hooks.get('context_hints', [])}")
    if runtime_hooks.get('required_context'):
        print(f"Required context: {runtime_hooks.get('required_context', [])}")
    if runtime_hooks.get('missing_context_hints'):
        print(f"Missing context hints: {runtime_hooks.get('missing_context_hints', [])}")
    if runtime_hooks.get('missing_required_context'):
        print(f"Missing required context: {runtime_hooks.get('missing_required_context', [])}")
    if runtime_hooks.get('available_context_keys'):
        print(f"Available context keys: {runtime_hooks.get('available_context_keys', [])}")
    profile_details = runtime_hooks.get('profile_details', {})
    if profile_details:
        print(f"Provider: {profile_details.get('provider', '-')}")
        if profile_details.get('command_examples'):
            print(f"Command examples: {profile_details.get('command_examples', [])}")
        if profile_details.get('required_context'):
            print(f"Required context: {profile_details.get('required_context', {})}")
        if profile_details.get('example_contexts'):
            print(f"Example contexts: {profile_details.get('example_contexts', {})}")
    print(f"Results: {len(runtime_hooks['results'])}")
    print(f"Evidências externas: {len(payload.get('external_evidence', {}).get('evidence_refs', []))}")
    if payload.get('ci_result'):
        print(f"CI result: {payload['ci_result'].get('ci_ref', '-')}")
    print(f"Próximo passo: {payload['run']['next_action']}")


def cmd_replan(args):
    payload = _service(args).replan(reason=args.reason)
    if args.json:
        _print_json(payload)
        return
    print(f"Replan registrado: {payload['decision']['action']}")
    print(f"Motivo: {payload['decision']['reason']}")
    print(f"Próximo passo: {payload['run']['next_action']}")


def cmd_events(args):
    events = _service(args).events(limit=args.limit, event_type=args.type)
    if args.json:
        _print_json(events)
        return
    for event in events:
        print(f"{event['timestamp']} {event['event_type']} ({event['actor']})")


def cmd_metrics(args):
    payload = _service(args).metrics()
    if args.json:
        _print_json(payload)
        return
    print(f"Projeto: {payload['project']}")
    print(f"Feature: {payload['feature']}")
    print(f"Lead time: {payload['lead_time']:.2f}h")
    print(f"Rounds: {payload['rounds']}")
    print(f"Pass rate: {payload['pass_rate']:.0%}")
    print(f"Custo: ${payload['custo']:.2f}")
    print(f"Falhas por tipo: {payload['falhas_por_tipo']}")
    if payload.get('runtime_provider_breakdown'):
        print(f"Runtime providers: {payload['runtime_provider_breakdown']}")


def cmd_classify(args):
    dims = _parse_json(args.dimensions, 'Dimensões')
    result = classify(
        project=args.project,
        demand=args.demand,
        dimensions=dims,
        rationale=args.rationale or '',
        override=args.override,
        override_reason=args.override_reason,
    )
    save_classification(result, Path(args.output))
    print(f"Classification saved: {result.mode} (score={result.total_score})")
    _print_json(result.to_dict())


def cmd_lint(args):
    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise CLIError(f"Arquivo spec não encontrado: {args.spec}")
    with open(spec_path) as f:
        spec = json.load(f)
    report = lint_spec(spec, mode=args.mode)
    save_lint_report(report, Path(args.output))
    print(f"Spec Lint: {report.result} (score={report.score})")
    for finding in report.findings:
        print(f"  [{finding['severity']}] {finding['rule']}: {finding['message']}")


def cmd_guard(args):
    authorized = _parse_json(args.authorized, 'Áreas autorizadas') if args.authorized else []
    prohibited = _parse_json(args.prohibited, 'Áreas proibidas') if args.prohibited else []
    guardian = ArchitectureGuardian(authorized_areas=authorized, prohibited_areas=prohibited)
    files = args.files.split(',') if args.files else []
    deps = args.dependencies.split(',') if args.dependencies else []
    report = guardian.check(changed_files=files, new_dependencies=deps)
    print(f"Architecture Guard: {report.result}")
    for violation in report.violations:
        print(f"  [{violation['severity']}] {violation['rule']}: {violation['message']}")


def cmd_drift(args):
    detector = DriftDetector(sprint_id=args.sprint or '')
    intake = prd = spec = sprint_plan = None
    if args.intake:
        with open(args.intake) as f:
            intake = json.load(f)
    if args.prd:
        with open(args.prd) as f:
            prd = json.load(f)
    if args.spec:
        with open(args.spec) as f:
            spec = json.load(f)
    if args.sprint_plan:
        with open(args.sprint_plan) as f:
            sprint_plan = json.load(f)
    report = detector.detect(intake=intake, prd=prd, spec=spec, sprint_plan=sprint_plan)
    print(f"Drift Detection: {report.result}")
    if report.findings:
        for finding in report.findings:
            print(f"  [{finding['severity']}] {finding['layer']}: {finding['finding']}")
    else:
        print('  Nenhum drift detectado.')


def cmd_progress_new(args):
    ledger = ProgressLedger.new(project=args.project, feature=args.feature, mode=args.mode)
    save_progress(ledger, Path(args.output))
    print(f"Progress ledger created: {args.output}")


def cmd_progress_update(args):
    input_path = Path(args.input)
    if not input_path.exists():
        raise CLIError(f"Arquivo progress não encontrado: {args.input}")
    ledger = load_progress(input_path)
    if args.gate:
        parts = args.gate.split('=')
        if len(parts) != 2:
            raise CLIError('Gate deve ter formato: GATE_N=state')
        ledger.update_gate(parts[0], parts[1])
    if args.status:
        ledger.set_status(args.status)
    if args.blocker:
        ledger.add_blocker(args.blocker)
    save_progress(ledger, Path(args.output))
    print(f"Progress updated: {args.output}")


def cmd_event_log(args):
    log = EventLog(Path(args.log))
    if args.add:
        parts = args.add.split('|')
        if len(parts) < 2:
            raise CLIError('Evento deve ter formato: event_type|actor|artifact_ref')
        event = Event.create(event_type=parts[0], actor=parts[1], artifact_ref=parts[2] if len(parts) > 2 else '')
        log.append(event)
        print(f"Event logged: {event.event_type}")
        return
    events = log.query(event_type=args.query) if args.query else log.query()
    for event in events:
        print(f"{event.timestamp} {event.event_type} ({event.actor})")


def cmd_handoff(args):
    handoff = create_handoff(
        source_artifact=args.source,
        source_version=args.version or 'v1',
        target_agent=args.target,
        objective=args.objective or '',
        restrictions=args.restrictions.split(',') if args.restrictions else [],
        open_questions=args.questions.split(',') if args.questions else [],
        required_evidences=args.evidences.split(',') if args.evidences else [],
    )
    with open(args.output, 'w') as f:
        json.dump(handoff.to_dict(), f, indent=2)
    print(f"Handoff created: {args.output}")


def cmd_template(args):
    data = _parse_json(args.data, 'Dados do template')
    if args.type == 'prd':
        print(render_prd(data))
    elif args.type == 'spec':
        print(render_spec(data))
    elif args.type == 'sprint':
        print(render_sprint_plan(data))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='cvg',
        description=(
            'CVG Harness CLI - operador canônico de demanda no terminal.\n\n'
            'Modo operador:\n'
            '  run, status, inspect, continue, pause, approve, dispatch, adapters, runtime-profiles, runtime, replan, events, metrics\n\n'
            'Modo avançado / engineering tools:\n'
            '  classify, lint, guard, drift, progress, event, handoff, template'
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    sub = parser.add_subparsers(dest='command')

    p_run = sub.add_parser('run', help='[operator] iniciar demanda e levar até sprint pronta para execução')
    p_run.add_argument('demand', help='Descrição da demanda')
    p_run.add_argument('--project', help='Nome do projeto; default = pasta atual')
    p_run.add_argument('--mode', default='AUTO', choices=['AUTO', 'ENTERPRISE'], help='AUTO usa heurística; ENTERPRISE força governança máxima')
    p_run.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_run.set_defaults(func=cmd_run)

    p_status = sub.add_parser('status', help='[operator] mostrar estado atual da demanda')
    p_status.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_status.add_argument('--json', action='store_true')
    p_status.set_defaults(func=cmd_status)

    p_inspect = sub.add_parser('inspect', help='[operator] inspecionar run atual ou sprint específica')
    p_inspect.add_argument('target', nargs='?', help='Sprint alvo, ex.: SPRINT-002')
    p_inspect.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_inspect.add_argument('--json', action='store_true')
    p_inspect.set_defaults(func=cmd_inspect)

    p_continue = sub.add_parser('continue', help='[operator] continuar a run a partir do último estado válido')
    p_continue.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_continue.add_argument('--changed-file', action='append', help='Arquivo alterado na sprint atual; repetir para múltiplos')
    p_continue.add_argument('--evidence', action='append', help='Evidência textual da sprint; repetir para múltiplas')
    p_continue.add_argument('--evidence-json', action='append', help='Evidência estruturada inline em JSON; repetir para múltiplas')
    p_continue.add_argument('--evidence-file', help='Arquivo JSON com evidências estruturadas')
    p_continue.add_argument('--round', type=int, default=1, help='Round atual da avaliação')
    p_continue.add_argument('--json', action='store_true')
    p_continue.set_defaults(func=cmd_continue)

    p_pause = sub.add_parser('pause', help='[operator] pausar a run atual')
    p_pause.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_pause.set_defaults(func=cmd_pause)

    p_approve = sub.add_parser('approve', help='[operator] aprovar sprint atual ou informada')
    p_approve.add_argument('target', nargs='?', help='Sprint alvo, ex.: SPRINT-002')
    p_approve.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_approve.set_defaults(func=cmd_approve)

    p_dispatch = sub.add_parser('dispatch', help='[operator] preparar hand-off explícito para executor externo')
    p_dispatch.add_argument('--executor', help='Nome do adapter externo conhecido')
    p_dispatch.add_argument('--capability', help='Capability desejada para auto-seleção do adapter')
    p_dispatch.add_argument('--context-json', help='Contexto JSON opcional para o dispatch externo')
    p_dispatch.add_argument('--repository', help='Atalho operador para repository em adapters/provider-aware')
    p_dispatch.add_argument('--ci-run-id', help='Atalho operador para ci_run_id em adapters/provider-aware')
    p_dispatch.add_argument('--ci-api', help='Atalho operador para ci_api em adapters/provider-aware')
    p_dispatch.add_argument('--ci-url', help='Atalho operador para ci_url em adapters/provider-aware')
    p_dispatch.add_argument('--ci-status', help='Atalho operador para ci_status em adapters/provider-aware')
    p_dispatch.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_dispatch.add_argument('--execute', action='store_true', help='Executa apenas adapters transport=cli; manual por padrão')
    p_dispatch.add_argument('--json', action='store_true')
    p_dispatch.set_defaults(func=cmd_dispatch)

    p_adapters = sub.add_parser('adapters', help='[operator] listar adapters externos conhecidos')
    p_adapters.add_argument('--capability', help='Capability para filtrar/ranquear adapters')
    p_adapters.add_argument('--repository', help='Atalho operador para repository em adapters/provider-aware')
    p_adapters.add_argument('--ci-run-id', help='Atalho operador para ci_run_id em adapters/provider-aware')
    p_adapters.add_argument('--ci-api', help='Atalho operador para ci_api em adapters/provider-aware')
    p_adapters.add_argument('--ci-url', help='Atalho operador para ci_url em adapters/provider-aware')
    p_adapters.add_argument('--ci-status', help='Atalho operador para ci_status em adapters/provider-aware')
    p_adapters.add_argument('--context-json', help='Contexto JSON opcional para ranquear adapters')
    p_adapters.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_adapters.add_argument('--json', action='store_true')
    p_adapters.set_defaults(func=cmd_adapters)

    p_runtime_profiles = sub.add_parser('runtime-profiles', help='[operator] listar perfis conhecidos de runtime/CI')
    p_runtime_profiles.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_runtime_profiles.add_argument('--json', action='store_true')
    p_runtime_profiles.set_defaults(func=cmd_runtime_profiles)

    p_runtime = sub.add_parser('runtime', help='[operator] executar hooks de runtime em modo opt-in')
    p_runtime.add_argument('--event', required=True, help='Evento do runtime, ex.: lint_trigger')
    p_runtime.add_argument('--context-json', help='Contexto JSON para placeholders dos hooks')
    p_runtime.add_argument('--repository', help='Atalho operador para repository em perfis como github-actions')
    p_runtime.add_argument('--ci-run-id', help='Atalho operador para ci_run_id em perfis de CI')
    p_runtime.add_argument('--ci-api', help='Atalho operador para ci_api em perfis como gitlab-ci')
    p_runtime.add_argument('--ci-url', help='Atalho operador para ci_url')
    p_runtime.add_argument('--ci-status', help='Atalho operador para ci_status')
    p_runtime.add_argument('--profile', default='default', help='Perfil de runtime conhecido; default = default')
    p_runtime.add_argument('--ci-result-json', help='CI result externo em JSON inline')
    p_runtime.add_argument('--ci-result-file', help='Arquivo JSON com CI result externo canônico')
    p_runtime.add_argument('--ci-result-url', help='URL JSON com CI result externo canônico')
    p_runtime.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_runtime.add_argument('--real', action='store_true', help='Executa hooks de verdade; por padrão é simulated')
    p_runtime.add_argument('--json', action='store_true')
    p_runtime.set_defaults(func=cmd_runtime)

    p_replan = sub.add_parser('replan', help='[operator] acionar replanejamento formal')
    p_replan.add_argument('--reason', required=True, help='Motivo do replanejamento')
    p_replan.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_replan.add_argument('--json', action='store_true')
    p_replan.set_defaults(func=cmd_replan)

    p_events = sub.add_parser('events', help='[operator] mostrar eventos relevantes da run atual')
    p_events.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_events.add_argument('--type', help='Filtrar por tipo de evento')
    p_events.add_argument('--limit', type=int, default=20)
    p_events.add_argument('--json', action='store_true')
    p_events.set_defaults(func=cmd_events)

    p_metrics = sub.add_parser('metrics', help='[operator] mostrar métricas atuais da demanda')
    p_metrics.add_argument('--workspace', help='Diretório base do projeto; default = cwd')
    p_metrics.add_argument('--json', action='store_true')
    p_metrics.set_defaults(func=cmd_metrics)

    p_classify = sub.add_parser('classify', help='[advanced] classificar demanda como FAST ou ENTERPRISE')
    p_classify.add_argument('--project', required=True, help='Nome do projeto')
    p_classify.add_argument('--demand', required=True, help='Descrição da demanda')
    p_classify.add_argument('--dimensions', help='JSON com dimensões de score')
    p_classify.add_argument('--rationale', help='Rationale da classificação')
    p_classify.add_argument('--override', action='store_true', help='Forçar modo ENTERPRISE')
    p_classify.add_argument('--override-reason', help='Motivo do override')
    p_classify.add_argument('--output', default='classification.json', help='Arquivo de saída')
    p_classify.set_defaults(func=cmd_classify)

    p_lint = sub.add_parser('lint', help='[advanced] executar spec linter')
    p_lint.add_argument('--spec', required=True, help='Caminho para spec.json')
    p_lint.add_argument('--mode', default='FAST', choices=['FAST', 'ENTERPRISE'])
    p_lint.add_argument('--output', default='spec-lint-report.json')
    p_lint.set_defaults(func=cmd_lint)

    p_guard = sub.add_parser('guard', help='[advanced] verificar aderência arquitetural')
    p_guard.add_argument('--files', help='Arquivos alterados (separados por vírgula)')
    p_guard.add_argument('--dependencies', help='Novas dependências (separadas por vírgula)')
    p_guard.add_argument('--authorized', help='JSON array com áreas autorizadas')
    p_guard.add_argument('--prohibited', help='JSON array com áreas proibidas')
    p_guard.set_defaults(func=cmd_guard)

    p_drift = sub.add_parser('drift', help='[advanced] detectar drift entre camadas')
    p_drift.add_argument('--sprint', help='ID da sprint')
    p_drift.add_argument('--intake', help='Caminho para intake.json')
    p_drift.add_argument('--prd', help='Caminho para prd.json')
    p_drift.add_argument('--spec', help='Caminho para spec.json')
    p_drift.add_argument('--sprint-plan', help='Caminho para sprint-plan.json')
    p_drift.set_defaults(func=cmd_drift)

    p_prog = sub.add_parser('progress', help='[advanced] gerenciar progress ledger')
    p_prog_sub = p_prog.add_subparsers(dest='progress_command')
    p_prog_new = p_prog_sub.add_parser('new', help='Criar novo ledger')
    p_prog_new.add_argument('--project', required=True)
    p_prog_new.add_argument('--feature', required=True)
    p_prog_new.add_argument('--mode', default='FAST', choices=['FAST', 'ENTERPRISE'])
    p_prog_new.add_argument('--output', default='progress.json')
    p_prog_new.set_defaults(func=cmd_progress_new)
    p_prog_upd = p_prog_sub.add_parser('update', help='Atualizar ledger')
    p_prog_upd.add_argument('--input', required=True)
    p_prog_upd.add_argument('--output', required=True)
    p_prog_upd.add_argument('--gate', help='Formato: GATE_N=state')
    p_prog_upd.add_argument('--status')
    p_prog_upd.add_argument('--blocker')
    p_prog_upd.set_defaults(func=cmd_progress_update)

    p_event = sub.add_parser('event', help='[advanced] gerenciar event log bruto')
    p_event.add_argument('--log', default='event-log.jsonl')
    p_event.add_argument('--add', help='Formato: event_type|actor|artifact_ref')
    p_event.add_argument('--query', help='Filtrar por tipo de evento')
    p_event.set_defaults(func=cmd_event_log)

    p_handoff = sub.add_parser('handoff', help='[advanced] criar contrato de handoff')
    p_handoff.add_argument('--source', required=True, help='Artefato fonte')
    p_handoff.add_argument('--version', help='Versão do artefato')
    p_handoff.add_argument('--target', required=True, help='Agente alvo')
    p_handoff.add_argument('--objective', help='Objetivo da próxima etapa')
    p_handoff.add_argument('--restrictions', help='Restrições (separadas por vírgula)')
    p_handoff.add_argument('--questions', help='Dúvidas abertas (separadas por vírgula)')
    p_handoff.add_argument('--evidences', help='Evidências requeridas (separadas por vírgula)')
    p_handoff.add_argument('--output', default='handoff.json')
    p_handoff.set_defaults(func=cmd_handoff)

    p_tpl = sub.add_parser('template', help='[advanced] renderizar template')
    p_tpl.add_argument('--type', required=True, choices=['prd', 'spec', 'sprint'], help='Tipo de template')
    p_tpl.add_argument('--data', help='Dados JSON para renderização')
    p_tpl.set_defaults(func=cmd_template)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, 'func'):
        try:
            args.func(args)
        except CLIError as exc:
            print(f"Erro: {exc}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError as exc:
            print(f"Erro: arquivo não encontrado: {exc}", file=sys.stderr)
            sys.exit(1)
        except ValueError as exc:
            print(f"Erro: {exc}", file=sys.stderr)
            sys.exit(1)
        except Exception as exc:
            print(f"Erro inesperado: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
