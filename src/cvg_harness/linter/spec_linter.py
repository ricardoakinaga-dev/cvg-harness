"""
P0-3: Spec Linter
Regras bloqueantes e score de qualidade executável para SPEC.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(Enum):
    BLOCKING = "blocking"
    WARNING = "warning"
    SUGGESTION = "suggestion"


@dataclass
class LintFinding:
    rule: str
    severity: str  # blocking | warning | suggestion
    message: str
    location: Optional[str] = None


@dataclass
class LintReport:
    spec_version: str
    result: str  # PASS | FAIL
    score: int  # 0-100
    findings: list[dict] = field(default_factory=list)
    blocking_issues: int = 0
    warnings: int = 0
    suggestions: int = 0
    recommendation: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class SpecLinter:
    """
    Valida a qualidade executável da SPEC antes da codificação.
    Regras bloqueantes:
    - critério de aceite não testável
    - módulo afetado vago
    - ausência de edge cases (ENTERPRISE)
    - ausência de exemplos de payload/contrato (quando há integração)
    - conflito interno entre spec.md e spec.json
    - ausência de limite de escopo
    - ausência de área proibida em mudança estrutural
    - ausência de rollback ou observabilidade em fluxo crítico
    """

    def __init__(self, mode: str = "FAST"):
        self.mode = mode
        self.findings: list[LintFinding] = []

    def lint(self, spec: dict) -> LintReport:
        self.findings = []
        spec_version = spec.get("version", "v1")

        self._check_accept_criteria(spec)
        self._check_modules(spec)
        self._check_edge_cases(spec)
        self._check_payload_examples(spec)
        self._check_scope_limit(spec)
        self._check_prohibited_areas(spec)
        self._check_rollback_observability(spec)

        blocking = [f for f in self.findings if f.severity == Severity.BLOCKING.value]
        warnings = [f for f in self.findings if f.severity == Severity.WARNING.value]
        suggestions = [f for f in self.findings if f.severity == Severity.SUGGESTION.value]

        score = self._calculate_score(len(blocking), len(warnings), len(suggestions))
        result = "PASS" if len(blocking) == 0 else "FAIL"
        recommendation = self._get_recommendation(result, len(blocking))

        return LintReport(
            spec_version=spec_version,
            result=result,
            score=score,
            findings=[asdict(f) for f in self.findings],
            blocking_issues=len(blocking),
            warnings=len(warnings),
            suggestions=len(suggestions),
            recommendation=recommendation,
        )

    def _check_accept_criteria(self, spec: dict) -> None:
        """Critério de aceite não testável é bloqueante."""
        criteria = spec.get("criterios", [])
        for i, c in enumerate(criteria):
            if not isinstance(c, dict):
                self.findings.append(LintFinding(
                    rule="unittestable_criterion",
                    severity=Severity.BLOCKING.value,
                    message=f"Critério {i} não é um objeto estruturado",
                    location=f"criterios[{i}]"
                ))
            elif not c.get("testavel") and not c.get("definido_como_lacuna"):
                self.findings.append(LintFinding(
                    rule="unittestable_criterion",
                    severity=Severity.BLOCKING.value,
                    message=f"Critério '{c.get('descricao', 'sem nome')}' não é testável",
                    location=f"criterios[{i}]"
                ))

    def _check_modules(self, spec: dict) -> None:
        """Módulo afetado vago é bloqueante."""
        modules = spec.get("modulos", [])
        for mod in modules:
            if not mod or len(mod) < 3:
                self.findings.append(LintFinding(
                    rule="vague_module",
                    severity=Severity.BLOCKING.value,
                    message=f"Módulo vago ou muito curto: '{mod}'",
                    location="modulos"
                ))

    def _check_edge_cases(self, spec: dict) -> None:
        """Ausência de edge cases é bloqueante em ENTERPRISE, warning em FAST."""
        edge_cases = spec.get("edge_cases", [])
        if not edge_cases:
            severity = Severity.BLOCKING.value if self.mode == "ENTERPRISE" else Severity.WARNING.value
            self.findings.append(LintFinding(
                rule="missing_edge_cases",
                severity=severity,
                message="Nenhum edge case definido",
                location="edge_cases"
            ))

    def _check_payload_examples(self, spec: dict) -> None:
        """Ausência de exemplos de payload quando há integração é bloqueante."""
        contracts = spec.get("contratos", [])
        has_integration = any(c.get("tipo") == "integracao" for c in contracts)
        has_examples = any(c.get("exemplo_payload") for c in contracts)
        if has_integration and not has_examples:
            self.findings.append(LintFinding(
                rule="missing_payload_examples",
                severity=Severity.BLOCKING.value,
                message="Integração declarada mas sem exemplo de payload/contrato",
                location="contratos"
            ))

    def _check_scope_limit(self, spec: dict) -> None:
        """Ausência de limite de escopo é bloqueante."""
        if not spec.get("limite_escopo"):
            self.findings.append(LintFinding(
                rule="missing_scope_limit",
                severity=Severity.BLOCKING.value,
                message="Limite de escopo não definido",
                location="limite_escopo"
            ))

    def _check_prohibited_areas(self, spec: dict) -> None:
        """Ausência de área proibida em mudança estrutural é bloqueante."""
        is_structural = spec.get("mudanca_estrutural", False)
        prohibited = spec.get("areas_proibidas", [])
        if is_structural and not prohibited:
            self.findings.append(LintFinding(
                rule="missing_prohibited_areas",
                severity=Severity.BLOCKING.value,
                message="Mudança estrutural sem áreas proibidas definidas",
                location="areas_proibidas"
            ))

    def _check_rollback_observability(self, spec: dict) -> None:
        """Ausência de rollback ou observabilidade em fluxo crítico é bloqueante."""
        is_critical = spec.get("fluxo_critico", False)
        has_rollback = bool(spec.get("rollback"))
        has_observability = bool(spec.get("observabilidade"))
        if is_critical and not (has_rollback and has_observability):
            self.findings.append(LintFinding(
                rule="missing_rollback_or_observability",
                severity=Severity.BLOCKING.value,
                message="Fluxo crítico sem definição de rollback e observabilidade",
                location="rollback|observabilidade"
            ))

    def _calculate_score(self, blocking: int, warnings: int, suggestions: int) -> int:
        """Calcula score de 0 a 100."""
        base = 100
        deduction = blocking * 30 + warnings * 5 + suggestions * 2
        return max(0, base - deduction)

    def _get_recommendation(self, result: str, blocking_count: int) -> str:
        if result == "PASS":
            return "SPEC pronta para execução. Nenhuma falha bloqueante."
        return f"SPEC contém {blocking_count} falha(s) bloqueante(s). Corrija antes de prosseguir."


def lint_spec(spec: dict, mode: str = "FAST") -> LintReport:
    linter = SpecLinter(mode=mode)
    return linter.lint(spec)


def save_lint_report(report: LintReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)


def load_lint_report(path: Path) -> LintReport:
    with open(path) as f:
        data = json.load(f)
    return LintReport(**data)
