"""
Sprint Planner - Quebra SPEC em sprints executáveis.
P0/P1 - Componente do fluxo de planejamento.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class Sprint:
    sprint_id: str
    escopo: str
    agente: str
    modulos: list[str] = field(default_factory=list)
    dependencias: list[str] = field(default_factory=list)
    criterios: list[str] = field(default_factory=list)
    evidencias: list[str] = field(default_factory=list)
    arquivos_esperados: list[str] = field(default_factory=list)
    risco: str = "medium"
    blocked_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SprintPlan:
    spec_ref: str
    spec_version: str
    mode: str
    sprints: list[Sprint] = field(default_factory=list)
    execution_order: list[str] = field(default_factory=list)  # sprint_ids em ordem
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["sprints"] = [s.to_dict() for s in self.sprints]
        return d


class SprintPlanner:
    """
    Quebra SPEC em sprints fechadas e gera execution order.
    Cada sprint deve ter:
    - escopo fechado
    - agente atribuído
    - dependências declaradas
    - evidências definidas
    """

    def plan(self, spec: dict, mode: str = "FAST") -> SprintPlan:
        """
        Gera sprint plan a partir de spec.json.
        Em modo FAST, uma sprint pode cobrir tudo.
        Em modo ENTERPRISE, quebra por módulo/contrato.
        """
        spec_version = spec.get("version", "v1")
        meta = spec.get("meta", "")
        modulos = spec.get("modulos", [])
        sprints = []

        if mode == "FAST":
            sprint = self._create_sprint(
                sprint_id="SPRINT-1",
                escopo=meta,
                agente="Coder Worker",
                modulos=modulos,
                spec=spec,
            )
            sprints.append(sprint)
            execution_order = ["SPRINT-1"]
        else:
            execution_order = self._plan_enterprise(modulos, spec, sprints)

        return SprintPlan(
            spec_ref=meta,
            spec_version=spec_version,
            mode=mode,
            sprints=sprints,
            execution_order=execution_order,
        )

    def _create_sprint(
        self,
        sprint_id: str,
        escopo: str,
        agente: str,
        modulos: list[str],
        spec: dict,
    ) -> Sprint:
        """Cria uma sprint com base na spec."""
        criterios = [c.get("descricao", "") for c in spec.get("criterios", [])]
        edge_cases = spec.get("edge_cases", [])
        evidences = [
            "implementação dos arquivos",
            "testes unitários",
            "logs de execução",
        ]
        risk = "low" if len(modulos) <= 1 else "medium" if len(modulos) <= 3 else "high"

        return Sprint(
            sprint_id=sprint_id,
            escopo=escopo,
            agente=agente,
            modulos=modulos,
            criterios=criterios,
            evidencias=evidences,
            arquivos_esperados=[f"src/{m}/" for m in modulos],
            risco=risk,
        )

    def _plan_enterprise(self, modulos: list[str], spec: dict, sprints: list) -> list[str]:
        """Plano para modo ENTERPRISE - quebra por módulo."""
        execution_order = []
        for i, mod in enumerate(modulos):
            sprint_id = f"SPRINT-{i + 1}"
            sprint = self._create_sprint(
                sprint_id=sprint_id,
                escopo=f"Implementar módulo {mod}",
                agente="Coder Worker",
                modulos=[mod],
                spec=spec,
            )
            sprint.dependencies = []
            if i > 0:
                sprint.blocked_by = [f"SPRINT-{i}"]
            sprints.append(sprint)
            execution_order.append(sprint_id)
        return execution_order

    def validate_sprint(self, sprint: Sprint, spec: dict) -> list[str]:
        """Valida se sprint está bem formada."""
        errors = []
        if not sprint.sprint_id:
            errors.append("sprint_id não pode ser vazio")
        if not sprint.escopo:
            errors.append("escopo não pode ser vazio")
        if not sprint.agente:
            errors.append("agente não pode ser vazio")
        if not sprint.criterios:
            errors.append("sprint deve ter critérios definidos")
        if not sprint.evidencias:
            errors.append("sprint deve ter evidências definidas")
        return errors


def save_sprint_plan(plan: SprintPlan, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(plan.to_dict(), f, indent=2)


def load_sprint_plan(path: Path) -> SprintPlan:
    with open(path) as f:
        data = json.load(f)
    sprints = [Sprint(**s) for s in data["sprints"]]
    data["sprints"] = sprints
    return SprintPlan(**data)
