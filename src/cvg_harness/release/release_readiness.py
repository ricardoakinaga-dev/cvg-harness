"""
Release Readiness Engine
Consolida decisão final de prontidão para promoção.
P1 - Componente do fluxo de release.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ReleaseGateStatus:
    gate: str
    status: str  # approved | rejected | waived | not_started
    blockers: list[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class ReleaseReadiness:
    project: str
    feature: str
    decision: str  # APPROVED | REJECTED | CONDITIONAL
    gates_summary: list[dict] = field(default_factory=list)
    missing_gates: list[str] = field(default_factory=list)
    exceptions: list[dict] = field(default_factory=list)
    residual_risks: list[str] = field(default_factory=list)
    waivers: list[dict] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class ReleaseReadinessEngine:
    """
    Decide se a entrega está pronta para promoção.
    Consolida gates, exceções e riscos residuais.
    """

    def assess(
        self,
        project: str,
        feature: str,
        gate_results: list[dict],
        evaluation_report: dict,
        drift_report: dict,
    ) -> ReleaseReadiness:
        """
        Avalia prontidão para release.
        """
        gates_summary = []
        all_approved = True
        has_blockers = False
        exceptions = []
        residual_risks = []
        waivers = []
        found_gates = set()

        for gate_result in gate_results:
            gate_name = gate_result.get("gate", "")
            found_gates.add(gate_name)
            # Aceita both state (canônico) e status (legacy) para compatibilidade
            state = gate_result.get("state") or gate_result.get("status", "not_started")
            blockers = gate_result.get("blockers", [])
            gates_summary.append({
                "gate": gate_name,
                "state": state,  # Canônico
                "blockers": blockers,
            })
            if state == "rejected":
                all_approved = False
                has_blockers = True
            elif state == "waived":
                waivers.append({
                    "gate": gate_name,
                    "reason": "waiver granted",
                    "blockers": blockers,
                })
                exceptions.append({
                    "gate": gate_name,
                    "reason": "waiver granted",
                    "blockers": blockers,
                })

        # Verificar gates obrigatórios faltantes
        required_gates = ["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5", "GATE_6", "GATE_7", "GATE_8", "GATE_9"]
        missing_gates = [g for g in required_gates if g not in found_gates]
        if missing_gates:
            has_blockers = True
            residual_risks.append(f"gates obrigatórios não encontrados: {missing_gates}")

        if evaluation_report.get("result") == "FAILED":
            has_blockers = True
            residual_risks.append("Avaliação funcional reprovou")

        if drift_report.get("result") == "DRIFT_DETECTED":
            blocking_severity = [f for f in drift_report.get("findings", []) if f.get("severity") in {"high", "critical"}]
            if blocking_severity:
                has_blockers = True
                residual_risks.append("Drift de alta severidade detectado")

        if has_blockers:
            decision = "REJECTED"
        elif exceptions:
            decision = "CONDITIONAL"
        else:
            decision = "APPROVED"

        return ReleaseReadiness(
            project=project,
            feature=feature,
            decision=decision,
            gates_summary=gates_summary,
            missing_gates=missing_gates,
            exceptions=exceptions,
            residual_risks=residual_risks,
            waivers=waivers,
        )


def save_release_readiness(report: ReleaseReadiness, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)


def load_release_readiness(path: Path) -> ReleaseReadiness:
    with open(path) as f:
        data = json.load(f)
    return ReleaseReadiness(**data)
