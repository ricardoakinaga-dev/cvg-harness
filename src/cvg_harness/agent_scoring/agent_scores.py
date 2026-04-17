"""
P2-2: Scoring por agente
Métricas de performance por agente baseadas no event log.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class AgentScore:
    agent: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    rounds_avg: float = 0.0
    pass_rate: float = 0.0
    blockers_caused: int = 0
    estimated_cost_usd: float = 0.0
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentScoreReport:
    project: str
    scores: dict[str, AgentScore] = field(default_factory=dict)
    top_performer: Optional[str] = None
    needs_improvement: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class AgentScoring:
    """Calcula score de performance por agente."""

    def __init__(self, project: str):
        self.project = project

    def score_from_events(self, event_log_path: Path) -> AgentScoreReport:
        from src.cvg_harness.ledger.event_log import load_events

        events = load_events(event_log_path)
        agent_stats: dict[str, dict] = defaultdict(lambda: {
            "completed": 0,
            "failed": 0,
            "rounds": [],
            "blockers": 0,
        })

        for e in events:
            actor = e.actor
            et = e.event_type

            if et == "sprint_approved":
                agent_stats[actor]["completed"] += 1
            elif et in ("sprint_failed", "evaluation_failed", "architecture_guard_failed"):
                agent_stats[actor]["failed"] += 1
            elif et == "replan_requested":
                agent_stats[actor]["blockers"] += 1

            round_sample = self._extract_round_sample(getattr(e, "metadata", {}))
            if round_sample is not None:
                agent_stats[actor]["rounds"].append(round_sample)

        scores: dict[str, AgentScore] = {}
        for agent, stats in agent_stats.items():
            total = stats["completed"] + stats["failed"]
            pass_rate = stats["completed"] / total if total > 0 else 0.0
            rounds_avg = (
                sum(stats["rounds"]) / len(stats["rounds"])
                if stats["rounds"]
                else (1.0 if total > 0 else 0.0)
            )
            scores[agent] = AgentScore(
                agent=agent,
                tasks_completed=stats["completed"],
                tasks_failed=stats["failed"],
                rounds_avg=rounds_avg,
                pass_rate=pass_rate,
                blockers_caused=stats["blockers"],
                estimated_cost_usd=self._estimate_cost(stats["failed"], stats["blockers"], rounds_avg),
            )

        pass_rates = sorted(scores.items(), key=lambda item: (-item[1].pass_rate, item[0]))
        top = pass_rates[0][0] if pass_rates else None
        needs_improvement = [agent for agent, score in pass_rates if score.pass_rate < 0.5]

        return AgentScoreReport(
            project=self.project,
            scores=scores,
            top_performer=top,
            needs_improvement=needs_improvement,
        )

    def _extract_round_sample(self, metadata: dict) -> Optional[float]:
        for key in ("round", "round_num", "round_number"):
            value = metadata.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        return None

    def _estimate_cost(self, failed: int, blockers: int, rounds_avg: float) -> float:
        """Estimativa conservadora de custo por agente."""
        base_cost = 50.0
        failure_cost = failed * 25.0
        blocker_cost = blockers * 10.0
        round_cost = max(rounds_avg - 1.0, 0.0) * 10.0
        return base_cost + failure_cost + blocker_cost + round_cost


def save_agent_scores(report: AgentScoreReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)


def load_agent_scores(path: Path) -> AgentScoreReport:
    with open(path) as f:
        data = json.load(f)
    scores = {k: AgentScore(**v) for k, v in data["scores"].items()}
    data["scores"] = scores
    return AgentScoreReport(**data)
