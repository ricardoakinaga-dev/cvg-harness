"""
Coder Worker Agent
Executa a sprint autorizada.
P0/P1 - Componente do fluxo de execução.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class CoderDeliverable:
    """Entrega do Coder Worker."""
    sprint_id: str
    arquivos_alterados: list[str] = field(default_factory=list)
    racional: str = ""
    evidencias: list[str] = field(default_factory=list)
    testes_passaram: bool = False
    lint_passou: bool = False
    issues: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class CoderWorker:
    """
    Executa a sprint autorizada.
    Regras:
    - Não redefine produto
    - Não amplia escopo
    - Não altera zona proibida
    """

    def __init__(self, authorized_areas: list[str], prohibited_areas: list[str]):
        self.authorized_areas = authorized_areas
        self.prohibited_areas = prohibited_areas

    def validate_scope(self, changed_files: list[str]) -> tuple[bool, list[str]]:
        """
        Valida se arquivos alterados estão dentro do escopo autorizado.
        Returns (is_valid, violations).
        """
        violations = []

        for file in changed_files:
            if any(prohibited in file for prohibited in self.prohibited_areas):
                violations.append(f"Arquivo em área proibida: {file}")

            if self.authorized_areas and not any(auth in file for auth in self.authorized_areas):
                violations.append(f"Arquivo fora da área autorizada: {file}")

        return len(violations) == 0, violations

    def deliver(
        self,
        sprint_id: str,
        arquivos_alterados: list[str],
        racional: str,
        evidencias: list[str],
        testes_passaram: bool = False,
        lint_passou: bool = False,
    ) -> CoderDeliverable:
        """
        Gera entrega da sprint.
        Valida escopo antes de entregar.
        """
        is_valid, violations = self.validate_scope(arquivos_alterados)

        return CoderDeliverable(
            sprint_id=sprint_id,
            arquivos_alterados=arquivos_alterados,
            racional=racional,
            evidencias=evidencias,
            testes_passaram=testes_passaram,
            lint_passou=lint_passou,
            issues=violations if not is_valid else [],
        )


def save_deliverable(deliverable: CoderDeliverable, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(deliverable.to_dict(), f, indent=2)


def load_deliverable(path: Path) -> CoderDeliverable:
    with open(path) as f:
        return CoderDeliverable(**json.load(f))
