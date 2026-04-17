#!/usr/bin/env python3
"""
Demo completo: CVG Harness End-to-End
Executa um fluxo completo do zero até a geração de artefatos.
Usa o FlowOrchestrator com métodos reais em vez de injeção manual de estado.

Leitura:
- Parte 1 a 10: execução canônica do fluxo real de negócio.
- Parte 9 (evidências): dados descritivos para manter o demo simples e didático.
  Não representam implementação de código real por arquivo, mas exercitam a decisão
  esperada pelo avaliador no contrato atual.

Este demo demonstra:
1. Fluxo completo com gates formais GATE_0 a GATE_9
2. Architecture Guardian validando áreas autorizadas
3. Drift Detection via orchestrator (avalia GATE_8)
4. Release Readiness consumindo gates reais
5. Métricas consolidadas de eventos reais
"""

import json
import tempfile
from pathlib import Path

from cvg_harness.flow import FlowOrchestrator
from cvg_harness.ledger.event_log import load_events


def run_demo():
    print("=" * 60)
    print("CVG Harness - Demo Completo End-to-End")
    print("=" * 60)

    # Setup workspace temporário
    tmpdir = Path(tempfile.mkdtemp(prefix="cvg-demo-"))
    print(f"\nWorkspace: {tmpdir}")

    # 1. Inicializar fluxo
    print("\n[1] INICIALIZAR FLUXO")
    print("-" * 40)
    orch = FlowOrchestrator(
        project="demo-project",
        feature="adição de autenticação OAuth2",
        mode="ENTERPRISE",
        workspace=tmpdir,
    )
    print(f"  Projeto: {orch.project}")
    print(f"  Feature: {orch.feature}")
    print(f"  Modo: {orch.mode}")
    print(f"  Fase: {orch.state.current_phase}")
    print(f"  Gate: {orch.state.current_gate}")

    # 2. Classificar demanda
    print("\n[2] CLASSIFICAR DEMANDA")
    print("-" * 40)
    dimensions = {
        "impacto_arquitetural": 3,
        "modulos_afetados": 2,
        "risco_de_regressao": 3,
        "criticidade_de_negocio": 3,
        "sensibilidade_de_dados": 3,
        "dependencia_externa": 2,
        "reversibilidade": 1,
        "complexidade_de_validacao": 2,
    }
    class_path = orch.classify(dimensions, "autenticação é crítica para segurança")
    with open(class_path) as f:
        classification = json.load(f)
    print(f"  Modo selecionado: {classification['mode']}")
    print(f"  Score total: {classification['total_score']}")

    # 3. Executar fluxo via orchestrator
    print("\n[3] EXECUTAR FLUXO (RESEARCH → PRD → SPEC)")
    print("-" * 40)

    # Research Agent
    research_md, system_map_md = orch.run_research()
    print(f"  Research gerado: {Path(research_md).name}")
    print(f"  System Map gerado: {Path(system_map_md).name}")

    # PRD Agent
    prd_md = orch.run_prd()
    print(f"  PRD gerado: {Path(prd_md).name}")

    # Spec Builder
    spec_md, spec_json = orch.build_spec()
    print(f"  SPEC gerada: {spec_md} e {spec_json}")

    # Verificar que os artefatos foram gerados corretamente
    with open(spec_json) as f:
        spec = json.load(f)
    print(f"  Módulos: {spec['modulos']}")
    print(f"  Áreas autorizadas: {spec['areas_autorizadas']}")
    print(f"  Áreas proibidas: {spec['areas_proibidas']}")

    # 4. Run Spec Lint
    print("\n[4] SPEC LINT")
    print("-" * 40)
    lint_result = orch.run_lint()
    print(f"  Resultado: {lint_result['result']}")
    print(f"  Score: {lint_result['score']}")
    if lint_result.get('blocking_issues'):
        print(f"  Falhas bloqueantes: {lint_result['blocking_issues']}")
    if lint_result.get('warnings'):
        print(f"  Warnings: {lint_result['warnings']}")
    if lint_result.get('findings'):
        for f in lint_result['findings']:
            print(f"    [{f['severity']}] {f['rule']}: {f['message']}")

    # 5. Sprint Planning (antes de guard para ter sprint plan)
    print("\n[5] SPRINT PLANNING")
    print("-" * 40)
    sprint_plan_path = orch.plan_sprints()
    print(f"  Sprint Plan gerado: {Path(sprint_plan_path).name}")

    # Verificar execution-order.json
    exec_order_path = tmpdir / "artifacts" / "execution-order.json"
    if exec_order_path.exists():
        with open(exec_order_path) as f:
            exec_order = json.load(f)
        print(f"  Execution Order: {exec_order['sequencia']}")

    # 6. Architecture Guard - arquivos autorizados (deve passar)
    print("\n[6] ARCHITECTURE GUARD (AREA AUTORIZADA)")
    print("-" * 40)
    guard_result = orch.check_guard(["src/auth/oauth2/token.py", "src/auth/session.py"])
    print(f"  Resultado: {guard_result['result']}")
    for v in guard_result['violations']:
        print(f"    [{v['severity']}] {v['rule']}: {v['message']}")

    # 7. Demonstrar guardian com área proibida (em fluxo separado para não contaminar)
    print("\n[7] ARCHITECTURE GUARD (AREA PROIBIDA - teste separado)")
    print("-" * 40)
    from cvg_harness.guardian.architecture_guardian import ArchitectureGuardian
    # Cria guardian isolated para testar área proibida
    isolated_guard = ArchitectureGuardian(
        authorized_areas=["src/auth/"],
        prohibited_areas=["src/legacy/"],
        boundaries=["src/legacy/", "src/v1/deprecated"],
    )
    isolated_result = isolated_guard.check(["src/legacy/auth/old_login.py"])
    print(f"  Resultado: {isolated_result.result}")
    for v in isolated_result.violations:
        v_dict = v if isinstance(v, dict) else vars(v)
        print(f"    [{v_dict['severity']}] {v_dict['rule']}: {v_dict['message']}")

    # 8. Drift Detection - via orchestrator (avalia GATE_8 formalmente)
    print("\n[8] DRIFT DETECTION")
    print("-" * 40)
    drift_dict = orch.detect_drift()
    print(f"  Resultado: {drift_dict['result']}")
    print(f"  Camadas verificadas: {drift_dict.get('layers_checked', [])}")
    for f in drift_dict.get('findings', []):
        print(f"  [{f['severity']}] {f.get('layer', 'unknown')}: {f.get('finding', f.get('message', ''))}")

    # 9. Sprint Evaluation com evidências
    # Observação de trilha: as evidências abaixo são descritivas para fins de demo.
    print("\n[9] SPRINT EVALUATION")
    print("-" * 40)
    # Evidências devem ser strings que aparecem nas expected_evidences do evaluator.
    # Em fluxo real, isso viria dos artefatos gerados durante a implementação.
    # Neste demo, usa-se lista descritiva para manter execução previsível e didática.
    evidence = [
        "implementação dos arquivos",
        "testes unitários",
        "logs de execução",
        "implementação do módulo auth",
        "testes do módulo auth",
    ]
    eval_result = orch.evaluate_sprint(evidence_files=evidence, round_num=1)
    print(f"  Resultado: {eval_result['result']}")
    print(f"  Próxima ação: {eval_result.get('next_action', 'none')}")
    if eval_result.get('evidence_missing'):
        print(f"  Evidências faltando: {eval_result['evidence_missing']}")

    # 10. Release Readiness
    print("\n[10] RELEASE READINESS")
    print("-" * 40)
    release_result = orch.check_release_readiness()
    print(f"  Decisão: {release_result['decision']}")
    print(f"  Gates avaliados: {len(release_result.get('gates_summary', []))}")
    for gs in release_result.get('gates_summary', []):
        print(f"    {gs['gate']}: {gs['state']}")
    if release_result.get('missing_gates'):
        print(f"  Gates faltantes: {release_result['missing_gates']}")
    if release_result.get('residual_risks'):
        print(f"  Riscos residuais: {release_result['residual_risks']}")
    if release_result.get('exceptions'):
        print(f"  Exceções: {release_result['exceptions']}")

    # 11. Flow State
    print("\n[11] FLOW STATE")
    print("-" * 40)
    flow_state_path = tmpdir / "flow-state.json"
    with open(flow_state_path) as f:
        flow_state = json.load(f)
    print(f"  Projeto: {flow_state['project']}")
    print(f"  Modo: {flow_state['mode']}")
    print(f"  Fase: {flow_state['current_phase']}")
    print(f"  Gate: {flow_state['current_gate']}")
    print(f"  Status: {flow_state['status']}")
    print(f"  Sprint: {flow_state['sprint_id']}")
    print(f"  Blockers: {flow_state['blockers']}")

    # 12. Event Log
    print("\n[12] EVENT LOG")
    print("-" * 40)
    events = load_events(tmpdir / "event-log.jsonl")
    print(f"  Total de eventos: {len(events)}")
    for e in events:
        print(f"  {e.timestamp} | {e.event_type} | {e.actor}")

    # 13. Métricas
    print("\n[13] MÉTRICAS")
    print("-" * 40)
    from cvg_harness.metrics_agg.metrics_aggregator import MetricsAggregator
    agg = MetricsAggregator()
    metrics_result = agg.aggregate(
        project="demo-project",
        feature="OAuth2 auth",
        mode="ENTERPRISE",
        event_log_path=tmpdir / "event-log.jsonl",
        progress_path=tmpdir / "progress.json",
    )
    print(f"  Lead time: {metrics_result.lead_time_hours:.2f}h")
    print(f"  Rounds: {metrics_result.total_rounds}")
    print(f"  Pass rate: {metrics_result.pass_rate:.0%}")
    print(f"  Custo: ${metrics_result.estimated_cost_usd:.2f}")
    print(f"  Falhas por tipo: {metrics_result.failures_by_type}")

    # 14. Fallback Policy Demo
    print("\n[14] FALLBACK POLICY")
    print("-" * 40)
    from cvg_harness.fallback.fallback_policy import FallbackPolicy
    policy = FallbackPolicy()

    for round_num in [1, 2, 3]:
        fb = policy.evaluate_evaluator_failure(round_count=round_num, spec={}, sprint={})
        print(f"  Round {round_num}: {fb.action} - {fb.details}")

    # 15. Final State
    print("\n[15] ESTADO FINAL")
    print("-" * 40)
    print(f"  Workspace: {tmpdir}")
    print(f"  Artefatos: {sorted([p.name for p in (tmpdir / 'artifacts').iterdir()])}")
    reports_dir = tmpdir / 'reports'
    if reports_dir.exists():
        print(f"  Relatórios: {sorted([p.name for p in reports_dir.iterdir()])}")
    print(f"  Gates persistidos: {sorted([p.name for p in (reports_dir / 'gates').iterdir()]) if (reports_dir / 'gates').exists() else []}")
    print(f"  Fluxo: {orch.state.status}")
    print(f"  Release: {release_result['decision']}")

    print("\n" + "=" * 60)
    # Mostrar resultado honesto
    print("  Observação de validação: trilha canônica de execução em `FlowOrchestrator` com")
    print("  saída final materializada em `release-readiness-report.json`; textos auxiliares")
    print("  em exemplos/sintéticos permanecem apenas para leitura humana.")

    if orch.state.status == "blocked":
        print("DEMO EXECUTADO - fluxo bloqueado em gate formal")
    elif release_result['decision'] == "REJECTED":
        print("DEMO EXECUTADO - release rejeitado")
    else:
        print(f"DEMO EXECUTADO - release: {release_result['decision']}")
    print("=" * 60)

    # Cleanup hint
    print(f"\n(Workspace preservado em: {tmpdir})")
    print("Para limpar: import shutil; shutil.rmtree(...)")

    return tmpdir


if __name__ == "__main__":
    run_demo()
