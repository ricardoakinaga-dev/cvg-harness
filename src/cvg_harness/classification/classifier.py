"""
P0-1: Classificador FAST vs ENTERPRISE
Gera classification.json com score por dimensão e decisão de modo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class ScoreLevel(Enum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3


DIMENSIONS = [
    "impacto_arquitetural",
    "modulos_afetados",
    "risco_de_regressao",
    "criticidade_de_negocio",
    "sensibilidade_de_dados",
    "dependencia_externa",
    "reversibilidade",
    "complexidade_de_validacao",
]


@dataclass
class ClassificationResult:
    project: str
    demand: str
    mode: str  # FAST | ENTERPRISE
    total_score: int
    dimensions: dict[str, int]
    rationale: str
    override_applied: bool = False
    override_reason: Optional[str] = None
    classified_by: str = "intake-classifier"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


def score_dimension(value: int) -> ScoreLevel:
    if value < 0:
        value = 0
    if value > 3:
        value = 3
    return ScoreLevel(value)


def calculate_mode(dimensions: dict[str, int], override_applied: bool = False) -> str:
    if override_applied:
        return "ENTERPRISE"
    total = sum(dimensions.values())
    has_critical = any(
        dimensions.get(d, 0) == 3
        for d in ["sensibilidade_de_dados", "impacto_arquitetural", "dependencia_externa", "criticidade_de_negocio"]
    )
    if total >= 9 or has_critical:
        return "ENTERPRISE"
    return "FAST"


def classify(
    project: str,
    demand: str,
    dimensions: dict[str, int],
    rationale: str,
    override: bool = False,
    override_reason: Optional[str] = None,
) -> ClassificationResult:
    """
    Classifica uma demanda como FAST ou ENTERPRISE.
    """
    for dim in DIMENSIONS:
        dimensions.setdefault(dim, 0)

    mode = calculate_mode(dimensions, override)
    total = sum(dimensions.values())

    return ClassificationResult(
        project=project,
        demand=demand,
        mode=mode,
        total_score=total,
        dimensions=dimensions,
        rationale=rationale,
        override_applied=override,
        override_reason=override_reason,
    )


def save_classification(result: ClassificationResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)


def load_classification(path: Path) -> ClassificationResult:
    with open(path) as f:
        data = json.load(f)
    return ClassificationResult(**data)


def validate_classification(result: ClassificationResult) -> list[str]:
    """Retorna lista de problemas. Lista vazia = válido."""
    errors = []
    if result.mode not in ("FAST", "ENTERPRISE"):
        errors.append(f"Modo inválido: {result.mode}")
    if result.total_score != sum(result.dimensions.values()):
        errors.append("total_score diverge da soma das dimensões")
    if not result.rationale:
        errors.append("rationale vazio")
    return errors
