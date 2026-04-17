"""
P2-1: Dashboards
Visualização do estado do fluxo via dados do progress ledger e event log.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class DashboardData:
    project: str
    feature: str
    mode: str
    status: str
    current_gate: str
    current_sprint: str
    gates_summary: dict[str, int] = field(default_factory=dict)  # approved, in_review, rejected, waived
    event_counts: dict[str, int] = field(default_factory=dict)
    metrics_summary: dict = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    recent_events: list[dict] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class Dashboard:
    """Gera visualização do estado operacional."""

    def __init__(self, project: str, feature: str, mode: str):
        self.project = project
        self.feature = feature
        self.mode = mode

    def build_from_progress_and_events(
        self,
        progress_path: Path,
        event_log_path: Path,
        metrics_path: Optional[Path] = None,
    ) -> DashboardData:
        from src.cvg_harness.ledger.progress_ledger import load_progress
        from src.cvg_harness.ledger.event_log import load_events
        from src.cvg_harness.metrics.metrics_catalog import load_metrics

        progress = load_progress(progress_path)
        events = load_events(event_log_path)
        metrics_summary = progress.metrics
        if metrics_path and metrics_path.exists():
            metrics_summary = load_metrics(metrics_path).to_dict()
        metrics_summary = self._enrich_metrics_summary(metrics_summary, progress.gates, progress.blockers, events)

        gates_summary = self._summarize_gates(progress.gates)
        event_counts = self._count_events(events)
        recent = events[-5:] if len(events) > 5 else events

        return DashboardData(
            project=self.project,
            feature=self.feature,
            mode=self.mode,
            status=progress.status,
            current_gate=progress.current_gate,
            current_sprint=progress.current_sprint,
            gates_summary=gates_summary,
            event_counts=event_counts,
            metrics_summary=metrics_summary,
            blockers=progress.blockers,
            recent_events=[e.to_dict() for e in recent],
        )

    def _summarize_gates(self, gates: dict[str, str]) -> dict[str, int]:
        counts = {"approved": 0, "in_review": 0, "rejected": 0, "not_started": 0, "waived": 0}
        for state in gates.values():
            if state in counts:
                counts[state] += 1
        return counts

    def _count_events(self, events: list) -> dict[str, int]:
        counts: dict[str, int] = {}
        for e in events:
            t = e.event_type
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _enrich_metrics_summary(self, metrics_summary, gates: dict[str, str], blockers: list[str], events: list) -> dict:
        summary = dict(metrics_summary) if isinstance(metrics_summary, dict) else {}
        retry_rounds = max(self._count_rounds(events) - 1, 0)
        replan_events = sum(1 for e in events if "replan" in e.event_type.lower())
        waiver_events = sum(1 for e in events if "waiver" in e.event_type.lower() or "waived" in e.event_type.lower())
        external_breakdown = {
            "requested": sum(1 for e in events if e.event_type == "external_execution_requested"),
            "planned": sum(1 for e in events if e.event_type == "external_executor_planned"),
            "dispatched": sum(1 for e in events if e.event_type == "external_executor_dispatched"),
            "failed": sum(1 for e in events if e.event_type == "external_execution_failed"),
            "ci_result": sum(1 for e in events if e.event_type == "ci_result_registered"),
        }
        runtime_signal_count = sum(1 for e in events if e.event_type == "runtime_hooks_executed")
        external_execution_signals = sum(external_breakdown.values()) + runtime_signal_count
        provider_breakdown: dict[str, int] = {}
        for e in events:
            if e.event_type not in {"runtime_hooks_executed", "ci_result_registered"}:
                continue
            metadata = getattr(e, "metadata", {}) or {}
            provider = str(metadata.get("provider") or "unknown")
            provider_breakdown[provider] = provider_breakdown.get(provider, 0) + 1
        structural_blockers: list[str] = []

        def add_unique(value: str) -> None:
            if value and value not in structural_blockers:
                structural_blockers.append(value)

        for gate, state in gates.items():
            if state == "rejected":
                add_unique(gate)
        for blocker in blockers:
            add_unique(blocker)

        summary.update(
            {
                "retry_rounds": retry_rounds,
                "replan_events": replan_events,
                "waiver_events": waiver_events,
                "external_execution_signals": external_execution_signals,
                "external_execution_breakdown": external_breakdown,
                "runtime_provider_breakdown": provider_breakdown,
                "structural_blockers_count": len(structural_blockers),
                "structural_blockers": structural_blockers,
            }
        )
        return summary

    def _count_rounds(self, events: list) -> int:
        rounds: set[float] = set()
        for e in events:
            metadata = getattr(e, "metadata", {}) or {}
            for key in ("round", "round_num", "round_number"):
                value = metadata.get(key)
                if isinstance(value, (int, float)):
                    rounds.add(float(value))
                    break
        return len(rounds)


def save_dashboard(dashboard: DashboardData, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(dashboard.to_dict(), f, indent=2)


def load_dashboard(path: Path) -> DashboardData:
    with open(path) as f:
        data = json.load(f)
    return DashboardData(**data)
