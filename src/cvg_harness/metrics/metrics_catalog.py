"""
P1-3: Catálogo de métricas
Métricas para gestão e melhoria contínua.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class DeliveryMetrics:
    project: str
    feature: str
    lead_time: float = 0.0  # horas
    rounds: int = 0
    retry_rounds: int = 0
    pass_rate: float = 0.0  # 0-1
    retrabalho: float = 0.0  # horas de retrabalho
    custo: float = 0.0  # USD
    falhas_por_tipo: dict[str, int] = field(default_factory=dict)
    sprints_count: int = 0
    gates_blocked: list[str] = field(default_factory=list)
    structural_blockers_count: int = 0
    structural_blockers: list[str] = field(default_factory=list)
    replan_events: int = 0
    waiver_events: int = 0
    external_execution_signals: int = 0
    external_execution_breakdown: dict[str, int] = field(default_factory=dict)
    runtime_provider_breakdown: dict[str, int] = field(default_factory=dict)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def add_failure(self, failure_type: str) -> None:
        self.falhas_por_tipo[failure_type] = self.falhas_por_tipo.get(failure_type, 0) + 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def calculate_pass_rate(self, total: int, passed: int) -> float:
        if total == 0:
            return 0.0
        self.pass_rate = passed / total
        return self.pass_rate


CATALOG_METRICS = {
    "lead_time": {"description": "Tempo total desde demanda até release", "unit": "horas"},
    "rounds": {"description": "Número de rodadas de feedback", "unit": "count"},
    "retry_rounds": {"description": "Rodadas adicionais além da primeira", "unit": "count"},
    "pass_rate": {"description": "Taxa de aprovação por sprint", "unit": "ratio"},
    "retrabalho": {"description": "Horas gastas em retrabalho", "unit": "horas"},
    "custo": {"description": "Custo estimado em USD", "unit": "USD"},
    "falhas_por_tipo": {"description": "Distribuição de tipos de falha", "unit": "dict"},
    "sprints_count": {"description": "Número de sprints executadas", "unit": "count"},
    "gates_blocked": {"description": "Gates que causaram bloqueio", "unit": "list"},
    "structural_blockers_count": {"description": "Bloqueios estruturais observados no fluxo", "unit": "count"},
    "structural_blockers": {"description": "Lista de bloqueios estruturais observados", "unit": "list"},
    "replan_events": {"description": "Sinais de replanejamento capturados", "unit": "count"},
    "waiver_events": {"description": "Sinais de waiver capturados", "unit": "count"},
    "external_execution_breakdown": {"description": "Quebra dos sinais de execução externa", "unit": "dict"},
    "runtime_provider_breakdown": {"description": "Quebra dos sinais de runtime por provider", "unit": "dict"},
}


def save_metrics(metrics: DeliveryMetrics, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics.to_dict(), f, indent=2)


def load_metrics(path: Path) -> DeliveryMetrics:
    with open(path) as f:
        data = json.load(f)
    return DeliveryMetrics(**data)
