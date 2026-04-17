"""
Metrics Aggregator Agent
Consolida dados para gestão e melhoria contínua.
P1 - Componente do fluxo de métricas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cvg_harness.metrics.metrics_catalog import DeliveryMetrics, save_metrics


@dataclass
class AgentMetrics:
    """Métricas de um agente específico."""
    agent: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_rounds: int = 0
    avg_rounds_per_task: float = 0.0
    pass_rate: float = 0.0
    blockers_caused: int = 0
    estimated_cost_usd: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SprintMetrics:
    """Métricas de uma sprint."""
    sprint_id: str
    duration_hours: float = 0.0
    rounds: int = 0
    passed: bool = False
    files_changed: int = 0
    blocked_gates: list[str] = field(default_factory=list)
    lead_time_hours: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AggregatedMetrics:
    """Métricas consolidadas do projeto."""
    project: str
    feature: str
    mode: str
    lead_time_hours: float = 0.0
    total_rounds: int = 0
    retry_rounds: int = 0
    pass_rate: float = 0.0
    retrabalho_hours: float = 0.0
    estimated_cost_usd: float = 0.0
    sprints_count: int = 0
    gates_blocked_count: int = 0
    blocked_gates: list[str] = field(default_factory=list)
    structural_blockers_count: int = 0
    structural_blockers: list[str] = field(default_factory=list)
    replan_events: int = 0
    waiver_events: int = 0
    external_execution_signals: int = 0
    external_execution_breakdown: dict[str, int] = field(default_factory=dict)
    runtime_provider_breakdown: dict[str, int] = field(default_factory=dict)
    failures_by_type: dict[str, int] = field(default_factory=dict)
    agent_metrics: dict[str, dict] = field(default_factory=dict)
    sprint_metrics: list[dict] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class MetricsAggregator:
    """
    Consolida métricas para gestão e melhoria contínua.
    Baseado em event log, progress ledger e sprint history.
    """

    def aggregate(
        self,
        project: str,
        feature: str,
        mode: str,
        event_log_path: Optional[Path] = None,
        progress_path: Optional[Path] = None,
    ) -> AggregatedMetrics:
        """
        Agrega métricas de múltiplas fontes.
        Métricas são calculadas a partir de eventos reais quando disponíveis.
        """
        from cvg_harness.ledger.event_log import load_events
        from cvg_harness.ledger.progress_ledger import load_progress

        events = []
        if event_log_path and event_log_path.exists():
            events = load_events(event_log_path)

        progress_data = {}
        if progress_path and progress_path.exists():
            progress_data = load_progress(progress_path)

        failures_by_type = self._count_failures(events)
        agent_metrics = self._aggregate_by_agent(events)
        total_rounds = self._count_unique_rounds(events)
        retry_rounds = max(total_rounds - 1, 0)
        replan_events = self._count_event_types(events, {"replan"})
        waiver_events = self._count_event_types(events, {"waiver", "waived"})
        external_execution_breakdown = {
            "requested": sum(1 for e in events if e.event_type == "external_execution_requested"),
            "planned": sum(1 for e in events if e.event_type == "external_executor_planned"),
            "dispatched": sum(1 for e in events if e.event_type == "external_executor_dispatched"),
            "failed": sum(1 for e in events if e.event_type == "external_execution_failed"),
            "evidence": sum(1 for e in events if e.event_type == "external_evidence_registered"),
            "ci_result": sum(1 for e in events if e.event_type == "ci_result_registered"),
        }
        runtime_provider_breakdown: dict[str, int] = {}
        for e in events:
            if e.event_type not in {"runtime_hooks_executed", "ci_result_registered"}:
                continue
            metadata = getattr(e, "metadata", {}) or {}
            provider = str(metadata.get("provider") or "unknown")
            runtime_provider_breakdown[provider] = runtime_provider_breakdown.get(provider, 0) + 1
        external_execution_signals = (
            external_execution_breakdown["requested"]
            + external_execution_breakdown["planned"]
            + external_execution_breakdown["dispatched"]
            + external_execution_breakdown["failed"]
            + external_execution_breakdown["evidence"]
            + external_execution_breakdown["ci_result"]
            + sum(1 for e in events if e.event_type == "runtime_hooks_executed")
        )

        pass_events = sum(1 for e in events if e.event_type in ("sprint_approved", "evaluation_passed"))
        total_eval = pass_events + sum(1 for e in events if "failed" in e.event_type)
        pass_rate = pass_events / total_eval if total_eval > 0 else 0.0
        # Happy path: release_approved with no failures = 100% pass rate
        has_release_approved = any(e.event_type == "release_approved" for e in events)
        if pass_rate == 0.0 and has_release_approved and total_rounds == 0:
            pass_rate = 1.0  # happy path: approved release with no retries

        # Calcular lead_time real a partir de timestamps de eventos
        lead_time_hours = self._calculate_lead_time(events)

        # Calcular retrabalho real: baseado em rounds de retry e replans
        retrabalho_hours = self._calculate_retrabalho(events)

        # Custo estimado vem dos metadados de progress se disponível
        # progress_data pode ser dict (None path ou legado) ou ProgressLedger
        if isinstance(progress_data, dict):
            estimated_cost_usd = progress_data.get("metrics", {}).get("estimatedCostUsd", 0.0)
            blocked_gates = [gate for gate, state in progress_data.get("gates", {}).items() if state == "rejected"]
        else:
            estimated_cost_usd = progress_data.metrics.get("estimatedCostUsd", 0.0)
            blocked_gates = [gate for gate, state in progress_data.gates.items() if state == "rejected"]
        structural_blockers = self._collect_structural_blockers(progress_data, blocked_gates)
        # Se não houver custo explícito, calcular a partir de sprints e rounds
        if estimated_cost_usd == 0.0 and events:
            estimated_cost_usd = self._estimate_cost_from_events(events)
            # Custo mínimo para fluxo aprovado sem métricas explícitas (demo/simulação)
            if estimated_cost_usd == 0.0 and has_release_approved and total_rounds == 0:
                estimated_cost_usd = 50.0  # custo base mínimo de sprint para fluxo aprovado

        return AggregatedMetrics(
            project=project,
            feature=feature,
            mode=mode,
            lead_time_hours=lead_time_hours,
            total_rounds=total_rounds,
            retry_rounds=retry_rounds,
            pass_rate=pass_rate,
            retrabalho_hours=retrabalho_hours,
            estimated_cost_usd=estimated_cost_usd,
            sprints_count=sum(1 for e in events if e.event_type == "sprint_started"),
            gates_blocked_count=len(blocked_gates),
            blocked_gates=blocked_gates,
            structural_blockers_count=len(structural_blockers),
            structural_blockers=structural_blockers,
            replan_events=replan_events,
            waiver_events=waiver_events,
            external_execution_signals=external_execution_signals,
            external_execution_breakdown=external_execution_breakdown,
            runtime_provider_breakdown=runtime_provider_breakdown,
            failures_by_type=failures_by_type,
            agent_metrics={k: v.to_dict() for k, v in agent_metrics.items()},
        )

    def export_delivery_metrics(
        self,
        project: str,
        feature: str,
        mode: str,
        output_path: Path,
        event_log_path: Optional[Path] = None,
        progress_path: Optional[Path] = None,
    ) -> DeliveryMetrics:
        """Gera e persiste o `delivery-metrics.json` canônico."""
        aggregated = self.aggregate(
            project=project,
            feature=feature,
            mode=mode,
            event_log_path=event_log_path,
            progress_path=progress_path,
        )
        delivery = self.to_delivery_metrics(aggregated)
        save_metrics(delivery, output_path)
        return delivery

    def to_delivery_metrics(self, aggregated: AggregatedMetrics) -> DeliveryMetrics:
        """Converte métricas agregadas para o contrato canônico de delivery-metrics.json."""
        return DeliveryMetrics(
            project=aggregated.project,
            feature=aggregated.feature,
            lead_time=aggregated.lead_time_hours,
            rounds=aggregated.total_rounds,
            retry_rounds=aggregated.retry_rounds,
            pass_rate=aggregated.pass_rate,
            retrabalho=aggregated.retrabalho_hours,
            custo=aggregated.estimated_cost_usd,
            falhas_por_tipo=aggregated.failures_by_type,
            sprints_count=aggregated.sprints_count,
            gates_blocked=aggregated.blocked_gates,
            structural_blockers_count=aggregated.structural_blockers_count,
            structural_blockers=aggregated.structural_blockers,
            replan_events=aggregated.replan_events,
            waiver_events=aggregated.waiver_events,
            external_execution_signals=aggregated.external_execution_signals,
            external_execution_breakdown=aggregated.external_execution_breakdown,
            runtime_provider_breakdown=aggregated.runtime_provider_breakdown,
        )

    def _calculate_lead_time(self, events: list) -> float:
        """Calcula lead time real a partir de timestamps de eventos."""
        if not events:
            return 0.0

        from datetime import datetime

        # Primeiro evento = início
        first_timestamp = None
        last_timestamp = None

        for e in events:
            if hasattr(e, 'timestamp') and e.timestamp:
                try:
                    ts = datetime.fromisoformat(e.timestamp.replace('Z', '+00:00'))
                    if first_timestamp is None or ts < first_timestamp:
                        first_timestamp = ts
                    if last_timestamp is None or ts > last_timestamp:
                        last_timestamp = ts
                except (ValueError, AttributeError):
                    pass

        if first_timestamp and last_timestamp:
            delta = last_timestamp - first_timestamp
            return delta.total_seconds() / 3600.0  # horas

        return 0.0

    def _calculate_retrabalho(self, events: list) -> float:
        """Calcula retrabalho real a partir de eventos de retry e replan."""
        retry_count = max(self._count_unique_rounds(events) - 1, 0)
        replan_count = self._count_event_types(events, {"replan"})
        # Cada retry/replan = ~2 horas de retrabalho estimado
        return (retry_count + replan_count) * 2.0

    def _estimate_cost_from_events(self, events: list) -> float:
        """Estima custo a partir de sprints e rodadas - método fallback."""
        sprints = sum(1 for e in events if e.event_type == "sprint_started")
        rounds = self._count_unique_rounds(events)
        # Custo base: $50 por sprint + $30 por round de retry
        return sprints * 50.0 + rounds * 30.0

    def _count_failures(self, events: list) -> dict[str, int]:
        """Conta falhas por tipo."""
        failures = {}
        for e in events:
            if "failed" in e.event_type or "rejected" in e.event_type:
                failures[e.event_type] = failures.get(e.event_type, 0) + 1
            if e.event_type in ("external_execution_failed", "external_executor_failed"):
                failures[e.event_type] = failures.get(e.event_type, 0) + 1
        return failures

    def _aggregate_by_agent(self, events: list) -> dict[str, AgentMetrics]:
        """Agrega métricas por agente."""
        from collections import defaultdict
        stats = defaultdict(lambda: {"completed": 0, "failed": 0, "rounds": set()})

        for e in events:
            if e.actor:
                if e.event_type in ("sprint_approved", "evaluation_passed"):
                    stats[e.actor]["completed"] += 1
                elif "failed" in e.event_type:
                    stats[e.actor]["failed"] += 1
                round_sample = self._extract_round_sample(getattr(e, "metadata", {}))
                if round_sample is not None:
                    stats[e.actor]["rounds"].add(round_sample)

        result = {}
        for agent, s in stats.items():
            total = s["completed"] + s["failed"]
            total_rounds = len(s["rounds"]) if s["rounds"] else total
            result[agent] = AgentMetrics(
                agent=agent,
                tasks_completed=s["completed"],
                tasks_failed=s["failed"],
                total_rounds=total_rounds,
                avg_rounds_per_task=total_rounds / total if total > 0 else 0.0,
                pass_rate=s["completed"] / total if total > 0 else 0.0,
                estimated_cost_usd=50.0 + (s["failed"] * 25.0) + (len(s["rounds"]) * 10.0),
            )
        return result

    def _extract_round_sample(self, metadata: dict) -> Optional[float]:
        for key in ("round", "round_num", "round_number"):
            value = metadata.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    def _count_unique_rounds(self, events: list) -> int:
        rounds = set()
        for e in events:
            round_sample = self._extract_round_sample(getattr(e, "metadata", {}))
            if round_sample is not None:
                rounds.add(round_sample)
        return len(rounds)

    def _count_event_types(self, events: list, fragments: set[str]) -> int:
        return sum(1 for e in events if any(fragment in e.event_type.lower() for fragment in fragments))

    def _collect_structural_blockers(self, progress_data, blocked_gates: list[str]) -> list[str]:
        blockers: list[str] = []

        def add_unique(value: str) -> None:
            if value and value not in blockers:
                blockers.append(value)

        for gate in blocked_gates:
            add_unique(gate)

        if isinstance(progress_data, dict):
            progress_blockers = progress_data.get("blockers", [])
        else:
            progress_blockers = getattr(progress_data, "blockers", [])

        for blocker in progress_blockers:
            add_unique(blocker)

        return blockers


def save_aggregated_metrics(metrics: AggregatedMetrics, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics.to_dict(), f, indent=2)


def load_aggregated_metrics(path: Path) -> AggregatedMetrics:
    with open(path) as f:
        data = json.load(f)
    if "agent_metrics" in data:
        data["agent_metrics"] = {k: AgentMetrics(**v) for k, v in data["agent_metrics"].items()}
    return AggregatedMetrics(**data)
