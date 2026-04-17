"""
Testes para Coder Worker, Replan Coordinator e Metrics Aggregator.
"""

import pytest
import tempfile
from pathlib import Path

from cvg_harness.coder.coder_worker import CoderWorker, CoderDeliverable, save_deliverable, load_deliverable
from cvg_harness.agent_scoring.agent_scores import AgentScoring, save_agent_scores, load_agent_scores
from cvg_harness.dashboard.dashboards import Dashboard, load_dashboard, save_dashboard
from cvg_harness.replan.replan_coordinator import ReplanCoordinator, ReplanDecision, ReplanTrigger
from cvg_harness.metrics_agg.metrics_aggregator import MetricsAggregator, AggregatedMetrics, save_aggregated_metrics, load_aggregated_metrics
from cvg_harness.ledger.event_log import Event, save_event
from cvg_harness.ledger.progress_ledger import ProgressLedger, save_progress
from cvg_harness.metrics.metrics_catalog import DeliveryMetrics, load_metrics, save_metrics
from cvg_harness.contracts.artifact_contracts import validate_artifact


def test_coder_worker_valid_scope():
    """Coder Worker valida escopo corretamente."""
    coder = CoderWorker(
        authorized_areas=["src/auth", "src/api"],
        prohibited_areas=["src/legacy", "src/v1"],
    )
    is_valid, violations = coder.validate_scope(["src/auth/login.py", "src/api/users.py"])
    assert is_valid
    assert violations == []


def test_coder_worker_prohibited_area():
    """Coder Worker bloqueia área proibida."""
    coder = CoderWorker(
        authorized_areas=["src/auth"],
        prohibited_areas=["src/legacy"],
    )
    is_valid, violations = coder.validate_scope(["src/legacy/old.py"])
    assert not is_valid
    assert len(violations) > 0


def test_coder_worker_outside_authorized():
    """Coder Worker rejeita arquivo fora da área autorizada."""
    coder = CoderWorker(
        authorized_areas=["src/auth"],
        prohibited_areas=["src/legacy"],
    )
    is_valid, violations = coder.validate_scope(["src/other/file.py"])
    assert not is_valid


def test_coder_worker_deliver():
    """Coder Worker gera entrega."""
    coder = CoderWorker(["src/auth"], ["src/legacy"])
    deliverable = coder.deliver(
        sprint_id="SPRINT-1",
        arquivos_alterados=["src/auth/login.py"],
        racional="implementou login",
        evidencias=["implementação", "testes"],
        testes_passaram=True,
        lint_passou=True,
    )
    assert deliverable.sprint_id == "SPRINT-1"
    assert len(deliverable.arquivos_alterados) == 1


def test_coder_deliverable_persistence():
    """Salva e carrega deliverable."""
    d = CoderDeliverable(
        sprint_id="SPRINT-1",
        arquivos_alterados=["a.py"],
        racional="test",
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        path = Path(f.name)
    save_deliverable(d, path)
    loaded = load_deliverable(path)
    assert loaded.sprint_id == "SPRINT-1"
    path.unlink()


def test_replan_evaluator_3_failures():
    """3 falhas do evaluator triggers rewrite_spec."""
    coordinator = ReplanCoordinator()
    decision = coordinator.evaluate(
        trigger=ReplanTrigger.EVALUATOR_FAILURES.value,
        context={"failures": 3},
    )
    assert decision.action == "rewrite_spec"


def test_replan_evaluator_2_failures():
    """2 falhas do evaluator triggers split_sprint."""
    coordinator = ReplanCoordinator()
    decision = coordinator.evaluate(
        trigger=ReplanTrigger.EVALUATOR_FAILURES.value,
        context={"failures": 2},
    )
    assert decision.action == "split_sprint"


def test_replan_arch_guard_failure():
    """Architecture guard failure triggers rewrite_spec."""
    coordinator = ReplanCoordinator()
    decision = coordinator.evaluate(
        trigger=ReplanTrigger.ARCHITECTURE_GUARD_FAILURES.value,
        context={},
    )
    assert decision.action == "rewrite_spec"


def test_replan_sprint_overflow():
    """Sprint overflow triggers split_sprint."""
    coordinator = ReplanCoordinator()
    decision = coordinator.evaluate(
        trigger=ReplanTrigger.SPRINT_OVERFLOW.value,
        context={},
    )
    assert decision.action == "split_sprint"


def test_replan_misclassification():
    """Misclassification triggers reclassify."""
    coordinator = ReplanCoordinator()
    decision = coordinator.evaluate(
        trigger=ReplanTrigger.MISCLASSIFICATION.value,
        context={},
        current_classification={"mode": "FAST"},
    )
    assert decision.action == "reclassify"


def test_metrics_aggregator_empty():
    """Metrics Aggregator funciona sem eventos."""
    agg = MetricsAggregator()
    metrics = agg.aggregate("proj", "feature", "FAST")
    assert metrics.project == "proj"
    assert metrics.mode == "FAST"
    assert metrics.pass_rate == 0.0


def test_metrics_aggregated_persistence():
    """Salva e carrega métricas agregadas."""
    metrics = AggregatedMetrics(
        project="proj",
        feature="feature",
        mode="FAST",
        lead_time_hours=10.0,
        pass_rate=0.85,
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        path = Path(f.name)
    save_aggregated_metrics(metrics, path)
    loaded = load_aggregated_metrics(path)
    assert loaded.project == "proj"
    assert loaded.pass_rate == 0.85
    path.unlink()


def test_metrics_aggregator_exports_delivery_metrics_contract(tmp_path: Path):
    """Metrics Aggregator gera delivery-metrics.json canônico a partir de eventos reais."""
    event_log_path = tmp_path / "event-log.jsonl"
    output_path = tmp_path / "delivery-metrics.json"

    for event_type in ["sprint_started", "evaluation_passed", "release_approved"]:
        save_event(
            Event.create(event_type, "FlowOrchestrator" if event_type == "sprint_started" else "Evaluator", "artifact-ref"),
            event_log_path,
        )

    agg = MetricsAggregator()
    delivery = agg.export_delivery_metrics(
        project="proj",
        feature="feature",
        mode="ENTERPRISE",
        event_log_path=event_log_path,
        output_path=output_path,
    )

    assert output_path.exists()
    loaded = load_metrics(output_path)
    assert loaded.project == "proj"
    assert loaded.pass_rate == 1.0
    assert delivery.custo >= 50.0
    assert validate_artifact("delivery-metrics.json", delivery.to_dict()) == []


def test_metrics_aggregator_counts_external_execution_signals(tmp_path: Path):
    """Metrics Aggregator reconhece sinal de execução externa quando existe."""
    event_log_path = tmp_path / "event-log.jsonl"
    output_path = tmp_path / "delivery-metrics.json"

    save_event(
        Event.create(
            "external_execution_requested",
            "OperatorService",
            "artifacts/external-dispatch-plan.json",
        ),
        event_log_path,
    )
    save_event(
        Event.create(
            "external_executor_planned",
            "OperatorService",
            "artifacts/external-dispatch-plan.json",
        ),
        event_log_path,
    )

    agg = MetricsAggregator()
    aggregated = agg.aggregate(
        project="proj",
        feature="feature",
        mode="ENTERPRISE",
        event_log_path=event_log_path,
    )
    delivery = agg.export_delivery_metrics(
        project="proj",
        feature="feature",
        mode="ENTERPRISE",
        event_log_path=event_log_path,
        output_path=output_path,
    )

    assert aggregated.external_execution_signals == 2
    assert aggregated.external_execution_breakdown == {"requested": 1, "planned": 1, "dispatched": 0, "failed": 0, "evidence": 0, "ci_result": 0}
    assert delivery.external_execution_signals == 2
    assert delivery.external_execution_breakdown["planned"] == 1
    assert output_path.exists()


def test_metrics_aggregator_counts_runtime_hooks_as_external_signal(tmp_path: Path):
    """Metrics Aggregator soma runtime hooks executados como sinal externo."""
    event_log_path = tmp_path / "event-log.jsonl"
    save_event(
        Event.create(
            "runtime_hooks_executed",
            "OperatorService",
            "artifacts/runtime-hooks.json",
        ),
        event_log_path,
    )

    agg = MetricsAggregator()
    aggregated = agg.aggregate(
        project="proj",
        feature="feature",
        mode="FAST",
        event_log_path=event_log_path,
    )

    assert aggregated.external_execution_signals == 1


def test_metrics_aggregator_counts_external_evidence_as_external_signal(tmp_path: Path):
    """Metrics Aggregator soma evidência externa registrada como sinal externo."""
    event_log_path = tmp_path / "event-log.jsonl"
    save_event(
        Event.create(
            "external_evidence_registered",
            "OperatorService",
            "artifacts/external-evidence-manifest.json",
        ),
        event_log_path,
    )

    agg = MetricsAggregator()
    aggregated = agg.aggregate(
        project="proj",
        feature="feature",
        mode="FAST",
        event_log_path=event_log_path,
    )

    assert aggregated.external_execution_signals == 1
    assert aggregated.external_execution_breakdown["evidence"] == 1


def test_metrics_aggregator_counts_ci_result_as_external_signal(tmp_path: Path):
    """Metrics Aggregator soma CI result como sinal externo."""
    event_log_path = tmp_path / "event-log.jsonl"
    save_event(
        Event.create(
            "ci_result_registered",
            "OperatorService",
            "artifacts/ci-result.json",
        ),
        event_log_path,
    )

    agg = MetricsAggregator()
    aggregated = agg.aggregate(
        project="proj",
        feature="feature",
        mode="FAST",
        event_log_path=event_log_path,
    )

    assert aggregated.external_execution_signals == 1
    assert aggregated.external_execution_breakdown["ci_result"] == 1


def test_metrics_aggregator_counts_runtime_provider_breakdown(tmp_path: Path):
    """Metrics Aggregator agrupa sinais de runtime por provider."""
    event_log_path = tmp_path / "event-log.jsonl"

    save_event(
        Event.create(
            "runtime_hooks_executed",
            "OperatorService",
            "artifacts/runtime-hooks.json",
            metadata={"provider": "github-actions"},
        ),
        event_log_path,
    )
    save_event(
        Event.create(
            "ci_result_registered",
            "OperatorService",
            "artifacts/ci-result.json",
            metadata={"provider": "gitlab-ci"},
        ),
        event_log_path,
    )

    agg = MetricsAggregator()
    aggregated = agg.aggregate(
        project="proj",
        feature="feature",
        mode="FAST",
        event_log_path=event_log_path,
    )

    assert aggregated.runtime_provider_breakdown == {"github-actions": 1, "gitlab-ci": 1}


def test_metrics_aggregator_tracks_unique_rounds_and_blocked_gates(tmp_path: Path):
    """Metrics Aggregator conta rounds, replan, waiver e bloqueios estruturais do progresso real."""
    event_log_path = tmp_path / "event-log.jsonl"
    progress_path = tmp_path / "progress.json"
    output_path = tmp_path / "delivery-metrics.json"

    save_event(
        Event.create("evaluation_failed", "Evaluator", "evaluation-report.json", metadata={"round": 1}),
        event_log_path,
    )
    save_event(
        Event.create("sprint_failed", "Evaluator", "evaluation-report.json", metadata={"round": 1}),
        event_log_path,
    )
    save_event(
        Event.create("sprint_approved", "Evaluator", "evaluation-report.json", metadata={"round": 2}),
        event_log_path,
    )
    save_event(
        Event.create("replan_requested", "ReplanCoordinator", "replan-decision.json", metadata={"round": 2}),
        event_log_path,
    )
    save_event(
        Event.create("waiver_granted", "waiver", "waiver.json", metadata={"round": 2}),
        event_log_path,
    )
    save_event(
        Event.create("gate_waived", "Evaluator", "gate-3.json", metadata={"round": 2}),
        event_log_path,
    )

    progress = ProgressLedger.new("proj", "feature", "ENTERPRISE")
    progress.blockers = ["arch_guard"]
    progress.update_gate("GATE_3", "rejected")
    save_progress(progress, progress_path)

    agg = MetricsAggregator()
    aggregated = agg.aggregate("proj", "feature", "ENTERPRISE", event_log_path=event_log_path, progress_path=progress_path)
    delivery = agg.export_delivery_metrics(
        project="proj",
        feature="feature",
        mode="ENTERPRISE",
        event_log_path=event_log_path,
        progress_path=progress_path,
        output_path=output_path,
    )

    assert aggregated.total_rounds == 2
    assert aggregated.retry_rounds == 1
    assert aggregated.gates_blocked_count == 1
    assert aggregated.blocked_gates == ["GATE_3"]
    assert aggregated.replan_events == 1
    assert aggregated.waiver_events == 2
    assert aggregated.structural_blockers_count == 2
    assert aggregated.structural_blockers == ["GATE_3", "arch_guard"]
    assert delivery.rounds == 2
    assert delivery.gates_blocked == ["GATE_3"]
    assert delivery.retry_rounds == 1
    assert delivery.replan_events == 1
    assert delivery.waiver_events == 2
    assert delivery.structural_blockers_count == 2
    assert output_path.exists()


def test_dashboard_counts_runtime_hooks_as_external_signal(tmp_path: Path):
    """Dashboard soma runtime hooks executados ao total de sinais externos."""
    progress_path = tmp_path / "progress.json"
    event_log_path = tmp_path / "event-log.jsonl"
    metrics_path = tmp_path / "delivery-metrics.json"

    progress = ProgressLedger.new("proj", "feature", "ENTERPRISE")
    save_progress(progress, progress_path)

    save_event(Event.create("runtime_hooks_executed", "Operator CLI", "artifacts/runtime-hooks.json"), event_log_path)

    save_metrics(
        DeliveryMetrics(project="proj", feature="feature"),
        metrics_path,
    )

    dashboard = Dashboard("proj", "feature", "ENTERPRISE")
    data = dashboard.build_from_progress_and_events(progress_path, event_log_path, metrics_path)

    assert data.metrics_summary["external_execution_signals"] == 1
    assert data.metrics_summary["external_execution_breakdown"] == {"requested": 0, "planned": 0, "dispatched": 0, "failed": 0, "ci_result": 0}


def test_dashboard_counts_runtime_provider_breakdown(tmp_path: Path):
    """Dashboard agrupa sinais de runtime por provider."""
    progress_path = tmp_path / "progress.json"
    event_log_path = tmp_path / "event-log.jsonl"
    metrics_path = tmp_path / "delivery-metrics.json"

    progress = ProgressLedger.new("proj", "feature", "ENTERPRISE")
    save_progress(progress, progress_path)

    save_event(
        Event.create(
            "runtime_hooks_executed",
            "Operator CLI",
            "artifacts/runtime-hooks.json",
            metadata={"provider": "github-actions"},
        ),
        event_log_path,
    )
    save_event(
        Event.create(
            "ci_result_registered",
            "Operator CLI",
            "artifacts/ci-result.json",
            metadata={"provider": "gitlab-ci"},
        ),
        event_log_path,
    )

    save_metrics(
        DeliveryMetrics(project="proj", feature="feature"),
        metrics_path,
    )

    dashboard = Dashboard("proj", "feature", "ENTERPRISE")
    data = dashboard.build_from_progress_and_events(progress_path, event_log_path, metrics_path)

    assert data.metrics_summary["runtime_provider_breakdown"] == {"github-actions": 1, "gitlab-ci": 1}


def test_dashboard_uses_realtime_workspace_artifacts(tmp_path: Path):
    """Dashboard nasce do workspace real e persiste como contrato canônico."""
    progress_path = tmp_path / "progress.json"
    event_log_path = tmp_path / "event-log.jsonl"
    metrics_path = tmp_path / "delivery-metrics.json"
    output_path = tmp_path / "dashboard.json"

    progress = ProgressLedger.new("proj", "feature", "ENTERPRISE")
    progress.current_gate = "GATE_3"
    progress.current_sprint = "SPRINT-7"
    progress.blockers = ["arch_guard"]
    progress.metrics = {"acceptancePassRate": 0.92, "estimatedCostUsd": 120.0}
    progress.update_gate("GATE_3", "approved")
    save_progress(progress, progress_path)

    save_event(Event.create("sprint_started", "FlowOrchestrator", "sprint-7"), event_log_path)
    save_event(Event.create("evaluation_passed", "Evaluator", "evaluation-report.json"), event_log_path)

    save_metrics(
        DeliveryMetrics(
            project="proj",
            feature="feature",
            lead_time=12.5,
            rounds=2,
            pass_rate=0.75,
            retrabalho=3.0,
            custo=120.0,
            falhas_por_tipo={"spec": 1},
            sprints_count=1,
            gates_blocked=["GATE_3"],
        ),
        metrics_path,
    )

    dashboard = Dashboard("proj", "feature", "ENTERPRISE")
    data = dashboard.build_from_progress_and_events(progress_path, event_log_path, metrics_path)
    save_dashboard(data, output_path)
    loaded = load_dashboard(output_path)

    assert loaded.project == "proj"
    assert loaded.current_gate == "GATE_3"
    assert loaded.event_counts["sprint_started"] == 1
    assert loaded.metrics_summary["pass_rate"] == 0.75
    assert loaded.metrics_summary["retry_rounds"] == 0
    assert loaded.metrics_summary["replan_events"] == 0
    assert loaded.metrics_summary["waiver_events"] == 0
    assert loaded.metrics_summary["external_execution_signals"] == 0
    assert loaded.metrics_summary["external_execution_breakdown"] == {"requested": 0, "planned": 0, "dispatched": 0, "failed": 0, "ci_result": 0}
    assert loaded.metrics_summary["structural_blockers_count"] == 1
    assert loaded.metrics_summary["structural_blockers"] == ["arch_guard"]
    assert loaded.blockers == ["arch_guard"]
    assert validate_artifact("dashboard.json", loaded.to_dict()) == []


def test_agent_scoring_ranks_agents_from_event_log(tmp_path: Path):
    """Agent scoring rankeia agentes a partir do event log real."""
    event_log_path = tmp_path / "event-log.jsonl"
    output_path = tmp_path / "agent-scores.json"

    events = [
        Event.create("sprint_approved", "Spec Builder", "spec.json", metadata={"round": 1}),
        Event.create("sprint_approved", "Spec Builder", "spec.json", metadata={"round": 2}),
        Event.create("evaluation_failed", "Evaluator", "evaluation-report.json", metadata={"round": 1}),
        Event.create("replan_requested", "Evaluator", "replan.json", metadata={"round": 2}),
    ]
    for event in events:
        save_event(event, event_log_path)

    scoring = AgentScoring("proj")
    report = scoring.score_from_events(event_log_path)
    save_agent_scores(report, output_path)
    loaded = load_agent_scores(output_path)

    assert report.top_performer == "Spec Builder"
    assert "Evaluator" in report.needs_improvement
    assert report.scores["Spec Builder"].rounds_avg == 1.5
    assert report.scores["Evaluator"].estimated_cost_usd > 50.0
    assert loaded.top_performer == "Spec Builder"
    assert loaded.scores["Evaluator"].tasks_failed == 1
