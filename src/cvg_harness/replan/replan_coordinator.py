"""
Replan Coordinator Agent
Aciona replanejamento formal quando o plano deixa de sustentar a execução.
P0/P1 - Componente do fluxo de replanejamento.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class ReplanTrigger(str, Enum):
    EVALUATOR_FAILURES = "evaluator_failures"
    ARCHITECTURE_GUARD_FAILURES = "architecture_guard_failures"
    SPEC_INVALID = "spec_invalid"
    SPRINT_OVERFLOW = "sprint_overflow"
    DRIFT_GRAVE = "drift_grave"
    MISCLASSIFICATION = "misclassification"
    MANUAL_REQUEST = "manual_request"


@dataclass
class ReplanDecision:
    """Decisão de replanejamento."""
    trigger: str
    action: str  # reschedule | reclassify | split_sprint | rewrite_spec | abort
    affected_artifacts: list[str] = field(default_factory=list)
    reason: str = ""
    blockers_cleared: list[str] = field(default_factory=list)
    new_plan: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class ReplanCoordinator:
    """
    Coordena replanejamento formal.
    Gatilhos: falha recorrente do evaluator, SPEC insuficiente,
    sprint superdimensionada, drift grave, classificação errada.
    """

    def evaluate(
        self,
        trigger: str,
        context: dict,
        current_spec: Optional[dict] = None,
        current_classification: Optional[dict] = None,
    ) -> ReplanDecision:
        """
        Avalia situação e decide ação de replanejamento.
        """
        if trigger == ReplanTrigger.EVALUATOR_FAILURES.value:
            failures = context.get("failures", 0)
            if failures >= 3:
                return ReplanDecision(
                    trigger=trigger,
                    action="rewrite_spec",
                    reason=f"{failures} falhas do evaluator - SPEC precisa ser reescrita",
                    affected_artifacts=["spec.json", "sprint-plan.json"],
                )
            elif failures >= 2:
                return ReplanDecision(
                    trigger=trigger,
                    action="split_sprint",
                    reason=f"{failures} falhas - sprint muito grande",
                    affected_artifacts=["sprint-plan.json"],
                )
            else:
                return ReplanDecision(
                    trigger=trigger,
                    action="reschedule",
                    reason="Poucas falhas - retry com feedback",
                    affected_artifacts=["sprint-plan.json"],
                )

        elif trigger == ReplanTrigger.ARCHITECTURE_GUARD_FAILURES.value:
            return ReplanDecision(
                trigger=trigger,
                action="rewrite_spec",
                reason="Falha arquitetural - escopo violou boundaries",
                affected_artifacts=["spec.json", "sprint-plan.json"],
                blockers_cleared=["architecture_guard_failed"],
            )

        elif trigger == ReplanTrigger.SPEC_INVALID.value:
            return ReplanDecision(
                trigger=trigger,
                action="rewrite_spec",
                reason="SPEC inválida durante execução",
                affected_artifacts=["spec.json", "prd.md"],
            )

        elif trigger == ReplanTrigger.SPRINT_OVERFLOW.value:
            return ReplanDecision(
                trigger=trigger,
                action="split_sprint",
                reason="Sprint explodiu escopo",
                affected_artifacts=["sprint-plan.json"],
            )

        elif trigger == ReplanTrigger.DRIFT_GRAVE.value:
            return ReplanDecision(
                trigger=trigger,
                action="rewrite_spec",
                reason="Drift grave detectado",
                affected_artifacts=["spec.json", "prd.md", "sprint-plan.json"],
            )

        elif trigger == ReplanTrigger.MISCLASSIFICATION.value:
            old_mode = current_classification.get("mode", "UNKNOWN") if current_classification else "UNKNOWN"
            return ReplanDecision(
                trigger=trigger,
                action="reclassify",
                reason=f"Classificação errada: {old_mode} -> ENTERPRISE",
                affected_artifacts=["classification.json", "spec.json"],
            )

        return ReplanDecision(
            trigger=trigger,
            action="reschedule",
            reason="Replanejamento genérico",
        )


def save_replan_decision(decision: ReplanDecision, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(decision.to_dict(), f, indent=2)


def load_replan_decision(path: Path) -> ReplanDecision:
    with open(path) as f:
        return ReplanDecision(**json.load(f))
