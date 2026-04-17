"""
P3-3: Inteligência comparativa entre projetos
Compara métricas e padrões entre projetos para identificar melhorias.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ProjectMetrics:
    project_id: str
    lead_time_hours: float
    pass_rate: float
    avg_rounds: float
    cost_usd: float
    sprints_count: int
    blockers_count: int
    mode: str
    domain: str = "unknown"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ComparisonResult:
    project_id: str
    benchmarks: dict[str, float]  # metric -> benchmark value
    percentile: dict[str, float]  # metric -> percentile (0-100)
    above_average: list[str]  # metrics where project is above benchmark
    below_average: list[str]  # metrics where project is below benchmark
    recommendations: list[str]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class ComparativeIntelligence:
    """
    Compara projeto contra benchmarks cross-projects.
    Identifica onde está acima ou abaixo da média.
    """

    def __init__(self, cross_project_metrics: list[ProjectMetrics]):
        self.cross_project = cross_project_metrics

    def _benchmarks(self) -> dict[str, float]:
        if not self.cross_project:
            return {}
        n = len(self.cross_project)
        return {
            "lead_time_hours": sum(p.lead_time_hours for p in self.cross_project) / n,
            "pass_rate": sum(p.pass_rate for p in self.cross_project) / n,
            "avg_rounds": sum(p.avg_rounds for p in self.cross_project) / n,
            "cost_usd": sum(p.cost_usd for p in self.cross_project) / n,
            "blockers_count": sum(p.blockers_count for p in self.cross_project) / n,
        }

    def _percentile(self, value: float, metric: str) -> float:
        if not self.cross_project:
            return 50.0
        values = [getattr(p, metric) for p in self.cross_project]
        below = sum(1 for v in values if v < value)
        return (below / len(values)) * 100

    def compare(self, project: ProjectMetrics) -> ComparisonResult:
        benchmarks = self._benchmarks()
        above = []
        below = []
        percentile = {}

        for metric, bench_val in benchmarks.items():
            proj_val = getattr(project, metric)
            pct = self._percentile(proj_val, metric)
            percentile[metric] = pct
            if metric == "lead_time_hours" or metric == "cost_usd" or metric == "avg_rounds" or metric == "blockers_count":
                if proj_val < bench_val:
                    above.append(metric)
                elif proj_val > bench_val:
                    below.append(metric)
            else:
                if proj_val > bench_val:
                    above.append(metric)
                elif proj_val < bench_val:
                    below.append(metric)

        recommendations = []
        if "lead_time_hours" in below:
            recommendations.append("Lead time acima da média: revisar escopo das sprints")
        if "pass_rate" in below:
            recommendations.append("Pass rate abaixo da média: melhorar qualidade da SPEC")
        if "blockers_count" in below:
            recommendations.append("Bloqueios frequentes: antecipar gates de revisão")

        return ComparisonResult(
            project_id=project.project_id,
            benchmarks=benchmarks,
            percentile=percentile,
            above_average=above,
            below_average=below,
            recommendations=recommendations,
        )


def save_comparison(result: ComparisonResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)


def load_comparison(path: Path) -> ComparisonResult:
    with open(path) as f:
        data = json.load(f)
    return ComparisonResult(**data)
