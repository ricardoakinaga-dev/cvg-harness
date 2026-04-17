"""
P0-7: Fallback formal
Política de falha 1, 2, 3 e regras de replan e waiver.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class FallbackAction(Enum):
    RETRY_LOCAL = "retry_local"
    REVIEW_SPRINT = "review_sprint"
    REPLAN = "replan"
    BLOCK = "block"


@dataclass
class FallbackEvent:
    trigger: str
    action: str
    round: int
    details: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class FallbackPolicy:
    """
    Política de fallback formal:
    1. Evaluator falha 1x -> retry local
    2. Evaluator falha 2x -> revisão de sprint
    3. Evaluator falha 3x -> replan formal obrigatório
    4. Architecture Guardian reprova -> block imediato
    5. Spec Lint reprova -> proibir execução
    6. Drift Detector inconsistency -> congelar sprint
    7. Sprint estoura escopo -> dividir sprint
    8. Complexidade mal classificada -> reclassificar
    9. SPEC inválida durante execução -> pausar e atualizar
    """

    def evaluate_evaluator_failure(self, round_count: int, spec: dict, sprint: dict) -> FallbackEvent:
        if round_count == 1:
            return FallbackEvent(
                trigger="evaluator_failure_round_1",
                action=FallbackAction.RETRY_LOCAL.value,
                round=round_count,
                details="Retornar ao coder com feedback fechado. Não alterar PRD ou classificação ainda.",
            )
        elif round_count == 2:
            return FallbackEvent(
                trigger="evaluator_failure_round_2",
                action=FallbackAction.REVIEW_SPRINT.value,
                round=round_count,
                details="Acionar revisão de sprint. Verificar se SPEC é insuficiente ou sprint está grande demais.",
            )
        else:
            return FallbackEvent(
                trigger="evaluator_failure_round_3",
                action=FallbackAction.REPLAN.value,
                round=round_count,
                details="Bloquear promoção. Acionar Replan Coordinator. Revisar classificação, SPEC e decomposição.",
            )

    def evaluate_arch_guard_failure(self) -> FallbackEvent:
        return FallbackEvent(
            trigger="architecture_guard_failed",
            action=FallbackAction.BLOCK.value,
            round=0,
            details="Bloquear imediatamente sprint. Impedir nova avaliação funcional até correção arquitetural.",
        )

    def evaluate_spec_lint_failure(self) -> FallbackEvent:
        return FallbackEvent(
            trigger="spec_lint_failed",
            action=FallbackAction.BLOCK.value,
            round=0,
            details="Proibir início da execução. Devolver para Spec Builder.",
        )

    def evaluate_drift_inconsistency(self, severity: str) -> FallbackEvent:
        return FallbackEvent(
            trigger=f"drift_detected_{severity}",
            action=FallbackAction.BLOCK.value,
            round=0,
            details=f"Congelar promoção da sprint. Drift {severity} detectado.",
        )

    def evaluate_scope_overflow(self, files_count: int, domains_count: int) -> FallbackEvent:
        return FallbackEvent(
            trigger="sprint_overflow",
            action=FallbackAction.REPLAN.value,
            round=0,
            details=f"Sprint explodiu: {files_count} arquivos, {domains_count} domínios. Dividir sprint.",
        )

    def evaluate_misclassification(self, current_mode: str, recommended_mode: str) -> FallbackEvent:
        return FallbackEvent(
            trigger="misclassification",
            action=FallbackAction.REPLAN.value,
            round=0,
            details=f"Classificação errada: {current_mode} -> {recommended_mode}. Migrar fluxo.",
        )

    def evaluate_spec_invalid_during_execution(self) -> FallbackEvent:
        return FallbackEvent(
            trigger="spec_invalid_during_execution",
            action=FallbackAction.BLOCK.value,
            round=0,
            details="Pausar sprint. Atualizar SPEC e versão. Rerodar Spec Lint.",
        )


def can_grant_waiver(waiver_data: dict) -> bool:
    """Verifica se waiver pode ser aceito."""
    required = ["dono", "prazo", "risco_residual"]
    for field in required:
        if field not in waiver_data or not waiver_data[field]:
            return False
    if waiver_data.get("risco_residual") == "critical":
        return False
    return True


@dataclass
class Waiver:
    dono: str
    prazo: str
    risco_residual: str
    justificativa: str
    artifact_ref: str
    granted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def save_fallback_event(event: FallbackEvent, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "a") as f:
        f.write(json.dumps(event.to_dict()) + "\n")


def load_fallback_events(path: Path) -> list[FallbackEvent]:
    if not path.exists():
        return []
    events = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(FallbackEvent(**json.loads(line)))
    return events
