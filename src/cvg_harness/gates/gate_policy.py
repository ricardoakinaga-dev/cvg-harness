"""
P0-6: Gates e política de aprovação
Estados formais e critérios objetivos por gate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from cvg_harness.types import GateState


@dataclass
class GateResult:
    gate: str
    state: str
    approver: str
    blockers: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


GATES = {
    "GATE_0": {
        "name": "Demanda classificada",
        "objective": "definir modo operacional e risco inicial",
        "input_artifact": "intake.md",
        "output_artifact": "classification.json",
        "approves_if": "score e racional completos",
        "rejects_if": "modo sem justificativa ou classificação inconsistente",
        "responsible": "Intake Classifier",
        "fallback": "reclassificar ou escalar para ENTERPRISE",
    },
    "GATE_1": {
        "name": "Research aprovado",
        "objective": "garantir base factual mínima",
        "input_artifact": "classification + codebase",
        "output_artifact": "research-notes.md, system-map.md",
        "approves_if": "riscos, módulos e restrições principais identificados",
        "rejects_if": "pesquisa superficial ou baseada em hipótese não marcada",
        "responsible": "Research Agent + planner técnico",
        "fallback": "nova rodada de research",
    },
    "GATE_2": {
        "name": "PRD aprovada",
        "objective": "validar problema, objetivo e limites",
        "input_artifact": "research",
        "output_artifact": "prd.md",
        "approves_if": "escopo e sucesso estão claros",
        "rejects_if": "problema mal definido ou fora de escopo inconsistente",
        "responsible": "owner de produto",
        "fallback": "revisão de escopo",
    },
    "GATE_3": {
        "name": "SPEC aprovada",
        "objective": "validar executabilidade técnica inicial",
        "input_artifact": "PRD + research",
        "output_artifact": "spec.md, spec.json",
        "approves_if": "critérios, limites e contratos principais existem",
        "rejects_if": "SPEC vaga ou incompleta",
        "responsible": "planner técnico",
        "fallback": "voltar ao Spec Builder",
    },
    "GATE_4": {
        "name": "Spec Lint aprovado",
        "objective": "eliminar ambiguidade e lacunas executáveis",
        "input_artifact": "SPEC",
        "output_artifact": "spec-lint-report.json",
        "approves_if": "zero falha bloqueante",
        "rejects_if": "ambiguidade, critério não testável ou lacuna crítica",
        "responsible": "Spec Linter",
        "fallback": "corrigir SPEC e rerodar lint",
    },
    "GATE_5": {
        "name": "Sprint pronta para execução",
        "objective": "garantir que a sprint cabe em execução controlada",
        "input_artifact": "SPEC aprovada e lintada",
        "output_artifact": "sprint-plan.json, execution-order.json",
        "approves_if": "sprint tem escopo fechado, agente, evidências e dependências claras",
        "rejects_if": "sprint ampla demais ou sem evidência definida",
        "responsible": "Sprint Planner",
        "fallback": "quebrar sprint ou replan",
    },
    "GATE_6": {
        "name": "Execução aderente à arquitetura",
        "objective": "impedir desvio estrutural durante a implementação",
        "input_artifact": "entrega da sprint",
        "output_artifact": "architecture-guard-report.json",
        "approves_if": "nenhuma violação sem waiver",
        "rejects_if": "boundary quebrado, acoplamento indevido ou área proibida tocada",
        "responsible": "Architecture Guardian",
        "fallback": "correção obrigatória ou replan",
    },
    "GATE_7": {
        "name": "Avaliação aprovada",
        "objective": "validar a sprint contra critérios e evidências",
        "input_artifact": "entrega + guard report",
        "output_artifact": "evaluation-report.json",
        "approves_if": "critérios obrigatórios aprovados",
        "rejects_if": "falha funcional, contratual ou de evidência",
        "responsible": "Evaluator",
        "fallback": "retorno ao coder ou replan",
    },
    "GATE_8": {
        "name": "Drift zerado ou aceito formalmente",
        "objective": "garantir alinhamento entre intenção, plano e execução",
        "input_artifact": "artefatos e avaliação",
        "output_artifact": "drift-report.json",
        "approves_if": "drift inexistente ou waiver formal justificado",
        "rejects_if": "desalinhamento grave sem aceite formal",
        "responsible": "Drift Detector + planner técnico",
        "fallback": "replan ou correção documental/execução",
    },
    "GATE_9": {
        "name": "Release readiness aprovada",
        "objective": "consolidar prontidão para promoção",
        "input_artifact": "todos os relatórios finais",
        "output_artifact": "release-readiness-report.json (canônico) + release-readiness.md (sidecar opcional)",
        "approves_if": "gates anteriores fechados e riscos residuais aceitáveis",
        "rejects_if": "há bloqueio aberto, evidência faltante ou exceção sem dono",
        "responsible": "Release Readiness Engine + owner técnico",
        "fallback": "segurar release e corrigir bloqueios",
    },
}


def evaluate_gate(gate_name: str, artifact_data: dict) -> GateResult:
    """Avalia um gate contra seus critérios."""
    gate_def = GATES.get(gate_name)
    if not gate_def:
        return GateResult(
            gate=gate_name,
            state=GateState.NOT_STARTED.value,
            approver="unknown",
            blockers=[f"Gate '{gate_name}' não existe"],
        )

    blockers = []

    if gate_name == "GATE_0":
        if not artifact_data.get("dimensions"):
            blockers.append("dimensions ausente")
        if artifact_data.get("total_score", 0) < 0:
            blockers.append("total_score inválido")
        if not artifact_data.get("rationale"):
            blockers.append("rationale ausente")
        if artifact_data.get("mode") not in ("FAST", "ENTERPRISE"):
            blockers.append(f"Modo inválido: {artifact_data.get('mode')}")

    elif gate_name == "GATE_1":
        if not artifact_data.get("fatos"):
            blockers.append("fatos ausentes")
        # Aceita modulos_impactados (research) ou modulos (spec/prd)
        has_modulos = bool(
            artifact_data.get("modulos")
            or artifact_data.get("modulos_impactados")
            or artifact_data.get("arquivos")
        )
        if not has_modulos:
            blockers.append("módulos não identificados")

    elif gate_name == "GATE_2":
        if not artifact_data.get("escopo"):
            blockers.append("escopo ausente")
        if not artifact_data.get("objetivo"):
            blockers.append("objetivo ausente")

    elif gate_name == "GATE_3":
        # SPEC: verifica criterios e modulos
        if not artifact_data.get("criterios"):
            blockers.append("critérios ausentes")
        if not artifact_data.get("modulos"):
            blockers.append("módulos ausentes")

    elif gate_name == "GATE_4":
        # Spec Lint: verifica resultado do lint (spec é avaliado, não o relatório)
        # artifact_data é o lint_report com result/score
        result = artifact_data.get("result", "")
        if result == "FAIL":
            blockers.append("lint encontrou falhas bloqueantes")
        elif result not in ("PASS", "FAIL"):
            blockers.append(f"resultado de lint inesperado: {result}")

    elif gate_name == "GATE_5":
        # Sprint planning: sprint-plan.json com sprints fechadas
        sprints = artifact_data.get("sprints", [])
        if not sprints:
            blockers.append("nenhuma sprint definida")
        else:
            for sp in sprints:
                if not sp.get("sprint_id"):
                    blockers.append("sprint sem ID")
                if not sp.get("agente"):
                    blockers.append(f"sprint {sp.get('sprint_id', '?')} sem agente definido")

    elif gate_name == "GATE_6":
        # Architecture guard: resultado deve ser PASS ou WAIVER
        result = artifact_data.get("result", "")
        if result == "FAIL":
            violations = artifact_data.get("violations", [])
            fail_violations = [v for v in violations if v.get("severity") == "fail"]
            if fail_violations:
                blockers.append(f"{len(fail_violations)} violação(ões) sem waiver")
        elif result not in ("PASS", "WAIVER"):
            blockers.append(f"resultado inesperado: {result}")

    elif gate_name == "GATE_7":
        # Evaluation: resultado deve ser PASSED
        result = artifact_data.get("result", "")
        if result == "FAILED":
            blockers.append("avaliação reprovou")
        elif result not in ("PASSED", "CONDITIONAL"):
            blockers.append(f"resultado inesperado: {result}")

    elif gate_name == "GATE_8":
        # Drift: não deve ter drift de alta severidade
        result = artifact_data.get("result", "")
        if result == "DRIFT_DETECTED":
            findings = artifact_data.get("findings", [])
            blocking_findings = [f for f in findings if f.get("severity") in {"high", "critical"}]
            if blocking_findings:
                blockers.append(f"drift de alta severidade: {len(blocking_findings)} achado(s)")
        elif result not in ("CLEAN", "DRIFT_DETECTED"):
            blockers.append(f"resultado inesperado: {result}")

    elif gate_name == "GATE_9":
        # Release readiness: todos os gates anteriores devem estar approved ou waived
        gates_summary = artifact_data.get("gates_summary", [])
        for gs in gates_summary:
            state = gs.get("state", "not_started")
            gate = gs.get("gate", "")
            if state == "rejected":
                blockers.append(f"gate {gate} rejeitado")

    # Support waived state when the upstream artifact explicitly marks a formal waiver
    result_marker = str(artifact_data.get("result", "")).upper()
    if blockers:
        state = GateState.REJECTED.value
    elif result_marker in {"WAIVER", "WAIVED"}:
        state = GateState.WAIVED.value
    else:
        state = GateState.APPROVED.value

    return GateResult(
        gate=gate_name,
        state=state,
        approver=gate_def["responsible"],
        blockers=blockers,
    )


def save_gate_result(result: GateResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result.to_dict(), f, indent=2)


def load_gate_result(path: Path) -> GateResult:
    with open(path) as f:
        data = json.load(f)
    return GateResult(**data)
