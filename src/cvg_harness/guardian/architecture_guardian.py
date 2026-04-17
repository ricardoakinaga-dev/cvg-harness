"""
P0-4: Architecture Guardian
Políticas de boundary e escopo para bloquear desvios estruturais.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


class GuardSeverity(Enum):
    PASS = "pass"
    FAIL = "fail"
    WAIVER = "waiver"


@dataclass
class GuardViolation:
    rule: str
    severity: str  # fail | waiver
    message: str
    area: str
    action: str


@dataclass
class GuardReport:
    sprint_id: str
    spec_ref: str
    result: str  # PASS | FAIL | WAIVER
    violations: list[dict] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class ArchitectureGuardian:
    """
    Bloqueia desvios arquiteturais durante a execução.
    Regras bloqueantes:
    - mudança em boundary não autorizada
    - criação de dependência circular
    - acoplamento de domínio indevido
    - alteração fora da zona autorizada
    - introdução de débito técnico não declarado
    """

    def __init__(
        self,
        authorized_areas: list[str],
        prohibited_areas: list[str],
        boundaries: Optional[list[str]] = None,
    ):
        self.authorized_areas = [self._normalize_path(area) for area in authorized_areas]
        self.prohibited_areas = [self._normalize_path(area) for area in prohibited_areas]
        self.boundaries = [self._normalize_path(boundary) for boundary in (boundaries or [])]
        self.violations: list[GuardViolation] = []

    def check(self, changed_files: list[str], new_dependencies: Optional[list[str]] = None) -> GuardReport:
        """
        Verifica se a execução está aderente à arquitetura.
        changed_files: lista de caminhos de arquivos alterados
        new_dependencies: lista de novas dependências detectadas
        """
        self.violations = []
        new_dependencies = new_dependencies or []
        normalized_files = [self._normalize_path(path) for path in changed_files]

        self._check_unauthorized_boundary_change(normalized_files)
        self._check_prohibited_area_touched(normalized_files)
        self._check_authorized_area_violated(normalized_files)
        self._check_circular_dependency(new_dependencies)
        self._check_domain_coupling(normalized_files)
        self._check_undeclared_tech_debt(new_dependencies)

        has_fail = any(v.severity == GuardSeverity.FAIL.value for v in self.violations)
        has_waiver = any(v.severity == GuardSeverity.WAIVER.value for v in self.violations)

        if has_fail:
            result = "FAIL"
        elif has_waiver:
            result = "WAIVER"
        else:
            result = "PASS"

        return GuardReport(
            sprint_id="",
            spec_ref="",
            result=result,
            violations=[asdict(v) for v in self.violations],
        )

    def _normalize_path(self, path: str) -> str:
        return path.strip().strip("/")

    def _matches_scope(self, path: str, scope: str) -> bool:
        normalized_path = self._normalize_path(path)
        normalized_scope = self._normalize_path(scope)
        return normalized_path == normalized_scope or normalized_path.startswith(f"{normalized_scope}/")

    def _matching_boundaries(self, file_path: str) -> list[str]:
        return [boundary for boundary in self.boundaries if self._matches_scope(file_path, boundary)]

    def _is_file_authorized(self, file_path: str) -> bool:
        return any(self._matches_scope(file_path, area) for area in self.authorized_areas)

    def _is_prohibited(self, file_path: str) -> bool:
        return any(self._matches_scope(file_path, area) for area in self.prohibited_areas)

    def _is_boundary_explicitly_authorized(self, boundary: str) -> bool:
        for area in self.authorized_areas:
            if area == boundary or area.startswith(f"{boundary}/"):
                return True
        return False

    def _check_unauthorized_boundary_change(self, changed_files: list[str]) -> None:
        """Boundary tocada sem autorização explícita exige fail ou waiver."""
        if not self.boundaries:
            return

        for file_path in changed_files:
            matched_boundaries = self._matching_boundaries(file_path)
            if not matched_boundaries:
                continue

            for boundary in matched_boundaries:
                if self._is_boundary_explicitly_authorized(boundary):
                    continue

                authorized_context = self._is_file_authorized(file_path)
                severity = GuardSeverity.WAIVER.value if authorized_context else GuardSeverity.FAIL.value
                action = (
                    "Registrar waiver formal para tocar esta boundary sensível ou estreitar a área autorizada na SPEC"
                    if authorized_context
                    else "Declarar explicitamente esta boundary na SPEC ou remover a alteração"
                )
                message = (
                    f"Arquivo {file_path} tocou boundary sensível '{boundary}' sem autorização explícita"
                )
                self.violations.append(GuardViolation(
                    rule="unauthorized_boundary_change",
                    severity=severity,
                    message=message,
                    area=boundary,
                    action=action,
                ))

    def _check_prohibited_area_touched(self, changed_files: list[str]) -> None:
        """Alteração em área proibida é bloqueante."""
        for file_path in changed_files:
            for prohibited in self.prohibited_areas:
                if self._matches_scope(file_path, prohibited):
                    self.violations.append(GuardViolation(
                        rule="prohibited_area_touched",
                        severity=GuardSeverity.FAIL.value,
                        message=f"Arquivo em área proibida: {file_path}",
                        area=prohibited,
                        action="Remover alteração ou requerer waiver formal fora deste fluxo",
                    ))

    def _check_authorized_area_violated(self, changed_files: list[str]) -> None:
        """Verifica se arquivos tocados estão fora das áreas autorizadas."""
        if not self.authorized_areas:
            return

        for file_path in changed_files:
            if self._is_prohibited(file_path):
                continue
            if self._is_file_authorized(file_path):
                continue
            if self._matching_boundaries(file_path):
                continue
            self.violations.append(GuardViolation(
                rule="outside_authorized_area",
                severity=GuardSeverity.FAIL.value,
                message=f"Arquivo fora da área autorizada: {file_path}",
                area=file_path,
                action="Verificar se este arquivo deve fazer parte do escopo aprovado",
            ))

    def _check_circular_dependency(self, new_dependencies: list[str]) -> None:
        """Criação de dependência circular é bloqueante."""
        normalized_dependencies = [dep.strip() for dep in new_dependencies]
        for dep in normalized_dependencies:
            if "->" not in dep:
                continue
            parts = dep.split("->")
            if len(parts) != 2:
                continue
            source, target = parts[0].strip(), parts[1].strip()
            reverse = f"{target} -> {source}"
            if reverse in normalized_dependencies:
                self.violations.append(GuardViolation(
                    rule="circular_dependency",
                    severity=GuardSeverity.FAIL.value,
                    message=f"Dependência circular detectada: {source} <-> {target}",
                    area=source,
                    action="Remover dependência circular e refatorar",
                ))

    def _extract_domain(self, path: str) -> Optional[str]:
        normalized = self._normalize_path(path)
        parts = normalized.split("/")
        if len(parts) < 2:
            return None
        if parts[0] == "src" and len(parts) > 1:
            return parts[1]
        return parts[0]

    def _check_domain_coupling(self, changed_files: list[str]) -> None:
        """Acoplamento de domínio indevido é bloqueante."""
        if not self.authorized_areas:
            return

        domains = {domain for domain in (self._extract_domain(area) for area in self.authorized_areas) if domain}
        if len(domains) <= 1:
            return

        for file_path in changed_files:
            if self._is_prohibited(file_path):
                continue
            file_domain = self._extract_domain(file_path)
            if file_domain and file_domain not in domains:
                self.violations.append(GuardViolation(
                    rule="domain_coupling",
                    severity=GuardSeverity.FAIL.value,
                    message=f"Arquivo {file_path} pertence a domínio diferente do autorizado",
                    area=file_domain,
                    action="Manter acoplamento dentro do domínio autorizado ou expandir o escopo formalmente",
                ))

    def _check_undeclared_tech_debt(self, new_dependencies: list[str]) -> None:
        """Débito técnico não declarado é falha obrigatória."""
        known_debt_markers = ["TODO", "FIXME", "HACK", "XXX", "DEPRECATED"]
        for dep in new_dependencies:
            if any(marker in dep.upper() for marker in known_debt_markers):
                self.violations.append(GuardViolation(
                    rule="undeclared_tech_debt",
                    severity=GuardSeverity.FAIL.value,
                    message=f"Débito técnico não declarado encontrado: {dep}",
                    area="",
                    action="Declarar débito técnico formalmente ou implementar imediatamente",
                ))


def save_guard_report(report: GuardReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)


def load_guard_report(path: Path) -> GuardReport:
    with open(path) as f:
        data = json.load(f)
    return GuardReport(**data)
