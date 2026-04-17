"""
P0-5: Drift Detector
Comparação entre camadas do fluxo para detectar desalinhamento.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DriftSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DriftFinding:
    layer: str
    finding: str
    severity: str  # low | medium | high | critical
    suspected_root_cause: str
    remediation: str


@dataclass
class DriftReport:
    sprint_id: str
    layers_checked: list[str]
    result: str  # CLEAN | DRIFT_DETECTED
    findings: list[dict] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class DriftDetector:
    """
    Detecta desalinhamento entre intenção, plano e execução.
    Camadas de drift:
    - intake x PRD
    - PRD x SPEC
    - SPEC x sprint plan
    - sprint plan x execução
    - execução x avaliação
    - avaliação x release readiness
    """

    def __init__(self, sprint_id: str = ""):
        self.sprint_id = sprint_id
        self.findings: list[DriftFinding] = []

    def detect(
        self,
        intake: Optional[dict] = None,
        prd: Optional[dict] = None,
        spec: Optional[dict] = None,
        sprint_plan: Optional[dict] = None,
        execution: Optional[dict] = None,
        evaluation: Optional[dict] = None,
        release_readiness: Optional[dict] = None,
    ) -> DriftReport:
        """Compara camadas e retorna relatório de drift."""
        self.findings = []
        layers_checked = []

        if intake and prd:
            layers_checked.append("intake_x_prd")
            self._check_intake_prd(intake, prd)

        if prd and spec:
            layers_checked.append("prd_x_spec")
            self._check_prd_spec(prd, spec)

        if spec and sprint_plan:
            layers_checked.append("spec_x_sprint_plan")
            self._check_spec_sprint_plan(spec, sprint_plan)

        if sprint_plan and execution:
            layers_checked.append("sprint_plan_x_execucao")
            self._check_sprint_plan_execution(sprint_plan, execution)

        if execution and evaluation:
            layers_checked.append("execucao_x_avaliacao")
            self._check_execution_evaluation(execution, evaluation)

        if evaluation and release_readiness:
            layers_checked.append("avaliacao_x_release_readiness")
            self._check_evaluation_release_readiness(evaluation, release_readiness)

        has_drift = len(self.findings) > 0
        result = "DRIFT_DETECTED" if has_drift else "CLEAN"

        return DriftReport(
            sprint_id=self.sprint_id,
            layers_checked=layers_checked,
            result=result,
            findings=[asdict(f) for f in self.findings],
        )

    def _add_finding(
        self,
        layer: str,
        finding: str,
        severity: DriftSeverity,
        suspected_root_cause: str,
        remediation: str,
    ) -> None:
        self.findings.append(DriftFinding(
            layer=layer,
            finding=finding,
            severity=severity.value,
            suspected_root_cause=suspected_root_cause,
            remediation=remediation,
        ))

    def _normalize_path(self, path: str) -> str:
        return path.strip().strip("/")

    def _matches_scope(self, path: str, scope: str) -> bool:
        normalized_path = self._normalize_path(path)
        normalized_scope = self._normalize_path(scope)
        return normalized_path == normalized_scope or normalized_path.startswith(f"{normalized_scope}/")

    def _normalize_state(self, value: str) -> str:
        return value.strip().lower() if value else ""

    def _check_intake_prd(self, intake: dict, prd: dict) -> None:
        intake_problem = intake.get("problema", "")
        prd_problem = prd.get("problema", "")
        if intake_problem and prd_problem and intake_problem != prd_problem:
            self._add_finding(
                layer="intake_x_prd",
                finding="Problema no intake difere do problema no PRD",
                severity=DriftSeverity.HIGH,
                suspected_root_cause="PRD divergiu da necessidade original sem justificativa",
                remediation="Revisar PRD contra intake original",
            )

    def _check_prd_spec(self, prd: dict, spec: dict) -> None:
        prd_objective = prd.get("objetivo", "")
        spec_objective = spec.get("meta", "") or spec.get("objetivo_tecnico", "")
        if prd_objective and spec_objective and prd_objective != spec_objective:
            self._add_finding(
                layer="prd_x_spec",
                finding="Objetivo do PRD difere da meta da SPEC",
                severity=DriftSeverity.HIGH,
                suspected_root_cause="SPEC não traduz corretamente o objetivo do PRD",
                remediation="Revisar SPEC contra PRD",
            )

    def _check_spec_sprint_plan(self, spec: dict, sprint_plan: dict) -> None:
        spec_modules = [self._normalize_path(module) for module in spec.get("modulos", [])]
        sprint_modules = [
            self._normalize_path(module)
            for sprint in sprint_plan.get("sprints", [])
            for module in sprint.get("modulos", [])
        ]
        if spec_modules and sprint_modules:
            missing = sorted(
                module for module in spec_modules
                if not any(self._matches_scope(sprint_module, module) for sprint_module in sprint_modules)
            )
            if missing:
                self._add_finding(
                    layer="spec_x_sprint_plan",
                    finding=f"Módulos na SPEC não estão no sprint plan: {missing}",
                    severity=DriftSeverity.MEDIUM,
                    suspected_root_cause="Sprint plan não cobre todos os módulos declarados na SPEC",
                    remediation="Atualizar sprint plan ou marcar módulos como fora de escopo com justificativa",
                )

    def _check_sprint_plan_execution(self, sprint_plan: dict, execution: dict) -> None:
        planned_files = set(sprint_plan.get("arquivos_esperados", []))
        executed_files = set(execution.get("arquivos_alterados", []))
        if planned_files and executed_files:
            extra = sorted(executed_files - planned_files)
            if extra:
                self._add_finding(
                    layer="sprint_plan_x_execucao",
                    finding=f"Arquivos alterados fora do planejado: {extra}",
                    severity=DriftSeverity.MEDIUM,
                    suspected_root_cause="Execução alterou arquivos não previstos no sprint plan",
                    remediation="Verificar expansão de escopo ou atualizar o plano formalmente",
                )

    def _check_execution_evaluation(self, execution: dict, evaluation: dict) -> None:
        evaluation_result = self._normalize_state(evaluation.get("result", ""))
        executed_files = set(execution.get("arquivos_alterados", []))
        planned_scope = execution.get("escopo_planejado", [])
        evidence_missing = evaluation.get("evidence_missing", [])

        if evaluation_result == "failed" and evidence_missing and not executed_files:
            self._add_finding(
                layer="execucao_x_avaliacao",
                finding="Avaliação falhou por evidência ausente, mas a execução não materializou arquivos alterados",
                severity=DriftSeverity.HIGH,
                suspected_root_cause="Execução não completou ou os outputs da sprint não foram capturados pelo fluxo",
                remediation="Verificar entrega do coder worker e persistência de artefatos/evidências da sprint",
            )

        if evaluation_result == "failed" and evidence_missing and executed_files:
            self._add_finding(
                layer="execucao_x_avaliacao",
                finding=f"Execução gerou arquivos, mas ainda faltam evidências para sustentar a avaliação: {evidence_missing}",
                severity=DriftSeverity.MEDIUM,
                suspected_root_cause="A implementação ocorreu, mas a trilha de testes/logs/artefatos comprobatórios ficou incompleta",
                remediation="Completar evidências faltantes ou ajustar o evaluator para consumir a trilha real produzida pela sprint",
            )

        if evaluation_result == "passed" and evidence_missing:
            self._add_finding(
                layer="execucao_x_avaliacao",
                finding=f"Avaliação aprovada apesar de evidências faltantes: {evidence_missing}",
                severity=DriftSeverity.HIGH,
                suspected_root_cause="A avaliação promoveu a sprint sem coerência entre resultado e evidências declaradas",
                remediation="Revisar evaluator e critérios para impedir aprovação com lacunas não justificadas",
            )

        if evaluation_result == "passed" and not executed_files and not evidence_missing:
            self._add_finding(
                layer="execucao_x_avaliacao",
                finding="Avaliação aprovada sem arquivos alterados ou execução materializada",
                severity=DriftSeverity.MEDIUM,
                suspected_root_cause="A trilha de execução não foi persistida mesmo com aprovação funcional",
                remediation="Persistir entregáveis de execução ou evidência material mínima antes da avaliação final",
            )

        if planned_scope and executed_files:
            outside_scope = sorted(
                file_path for file_path in executed_files
                if not any(self._matches_scope(file_path, scope) for scope in planned_scope if scope)
            )
            if outside_scope:
                self._add_finding(
                    layer="execucao_x_avaliacao",
                    finding=f"Arquivos executados fora do escopo planejado: {outside_scope}",
                    severity=DriftSeverity.MEDIUM,
                    suspected_root_cause="Execução desviou do escopo autorizado da sprint",
                    remediation="Verificar se houve expansão de escopo, replan ou atualização pendente da SPEC/sprint plan",
                )

    def _check_evaluation_release_readiness(
        self, evaluation: dict, release_readiness: dict
    ) -> None:
        eval_result = self._normalize_state(evaluation.get("result", ""))
        release_decision = self._normalize_state(release_readiness.get("decision", ""))
        evidence_missing = evaluation.get("evidence_missing", [])
        residual_risks = release_readiness.get("residual_risks", [])
        missing_gates = release_readiness.get("missing_gates", [])

        if eval_result == "failed" and release_decision == "approved":
            self._add_finding(
                layer="avaliacao_x_release_readiness",
                finding="Avaliação reprovou mas release readiness aprovou",
                severity=DriftSeverity.CRITICAL,
                suspected_root_cause="Release aprovou sem considerar a reprovação funcional/técnica da sprint",
                remediation="Revisar imediatamente a decisão de release e bloquear promoção até a avaliação passar",
            )
        elif eval_result == "failed" and release_decision == "conditional":
            self._add_finding(
                layer="avaliacao_x_release_readiness",
                finding="Avaliação reprovou e release permaneceu apenas condicional",
                severity=DriftSeverity.HIGH,
                suspected_root_cause="A reprovação da avaliação foi tratada como risco residual em vez de blocker de promoção",
                remediation="Converter reprovação da avaliação em bloqueio explícito do release",
            )

        if eval_result == "passed" and release_decision == "rejected" and not missing_gates:
            self._add_finding(
                layer="avaliacao_x_release_readiness",
                finding="Avaliação aprovou mas release readiness rejeitou sem gates faltantes declarados",
                severity=DriftSeverity.MEDIUM,
                suspected_root_cause="Release rejeitou por critério não refletido em gates, riscos ou exceções persistidas",
                remediation="Explicitar blockers do release em residual_risks, exceptions ou gates_summary",
            )

        gates_summary = release_readiness.get("gates_summary", [])
        for gate_summary in gates_summary:
            gate_state = self._normalize_state(gate_summary.get("state", "not_started"))
            gate_name = gate_summary.get("gate", "")
            if gate_state == "rejected" and release_decision != "rejected":
                severity = DriftSeverity.CRITICAL if gate_name in {"GATE_7", "GATE_8", "GATE_9"} else DriftSeverity.HIGH
                self._add_finding(
                    layer="avaliacao_x_release_readiness",
                    finding=f"{gate_name} rejeitado mas release permaneceu {release_decision.upper() or 'sem decisão'}",
                    severity=severity,
                    suspected_root_cause="Gate rejeitado não foi tratado como blocker coerente na decisão final de release",
                    remediation="Bloquear release até o gate rejeitado ser resolvido, waived formalmente ou refletido como exceção explícita",
                )

        if evidence_missing and not residual_risks:
            self._add_finding(
                layer="avaliacao_x_release_readiness",
                finding=f"Evidências faltando sem risco residual declarado: {evidence_missing}",
                severity=DriftSeverity.MEDIUM,
                suspected_root_cause="Release não reconhece evidências faltantes como risco operacional ou funcional",
                remediation="Declarar risco residual compatível ou anexar as evidências pendentes antes da promoção",
            )

        if missing_gates and release_decision == "approved":
            self._add_finding(
                layer="avaliacao_x_release_readiness",
                finding=f"Release aprovado com gates obrigatórios faltantes: {missing_gates}",
                severity=DriftSeverity.CRITICAL,
                suspected_root_cause="Decisão de release foi emitida antes da consolidação completa dos gates obrigatórios",
                remediation="Reexecutar release readiness somente após persistência de todos os gates obrigatórios",
            )


def save_drift_report(report: DriftReport, output_path) -> None:
    with open(output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)


def load_drift_report(path) -> DriftReport:
    with open(path) as f:
        data = json.load(f)
    return DriftReport(**data)
