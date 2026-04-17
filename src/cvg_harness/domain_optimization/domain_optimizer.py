"""
P3-2: Otimização por domínio
Sugere otimizações baseadas no domínio do projeto.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class DomainOptimization:
    domain: str
    suggested_mode: str
    suggested_gates: list[str]
    recommended_policies: list[str]
    warnings: list[str]
    hints: list[str]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


DOMAIN_OPTIMIZATIONS = {
    "web_backend": DomainOptimization(
        domain="web_backend",
        suggested_mode="ENTERPRISE",
        suggested_gates=["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5", "GATE_6", "GATE_7", "GATE_8", "GATE_9"],
        recommended_policies=["strict_contract_validation", "rollback_mandatory", "ci_integration"],
        warnings=["integração com banco de dados requer validação de schema"],
        hints=["use lint para API contracts", "architecture guardian para camadas"],
    ),
    "frontend_react": DomainOptimization(
        domain="frontend_react",
        suggested_mode="FAST",
        suggested_gates=["GATE_0", "GATE_3", "GATE_4", "GATE_7"],
        recommended_policies=["component_contract", "visual_regression"],
        warnings=["componentes compartilhados exigem validação extra"],
        hints=["spec deve incluir casos visuais", "use storybook como evidência"],
    ),
    "data_pipeline": DomainOptimization(
        domain="data_pipeline",
        suggested_mode="ENTERPRISE",
        suggested_gates=["GATE_0", "GATE_1", "GATE_2", "GATE_3", "GATE_4", "GATE_5", "GATE_6", "GATE_7", "GATE_8", "GATE_9"],
        recommended_policies=["data_quality_gates", "lineage_tracking", "rollback_data"],
        warnings=["transformações de dados são difíceis de reverter"],
        hints=["drift detector essencial", "testes de qualidade de dados"],
    ),
    "cli_tool": DomainOptimization(
        domain="cli_tool",
        suggested_mode="FAST",
        suggested_gates=["GATE_0", "GATE_3", "GATE_5", "GATE_7"],
        recommended_policies=["output_contract", "error_exit_codes"],
        warnings=["CLI quebra em pipeline"],
        hints=["spec deve definir output estável", "testes de integração"],
    ),
    "library": DomainOptimization(
        domain="library",
        suggested_mode="ENTERPRISE",
        suggested_gates=["GATE_0", "GATE_1", "GATE_3", "GATE_4", "GATE_6", "GATE_7", "GATE_8"],
        recommended_policies=["semantic_version", "api_contract", "changelog"],
        warnings=["mudar API pública quebra consumidores"],
        hints=["versioning obrigatório", "deprecação gradual"],
    ),
}


def get_optimization(domain: str) -> Optional[DomainOptimization]:
    return DOMAIN_OPTIMIZATIONS.get(domain)


def suggest_domain_from_modules(modules: list[str]) -> str:
    """Infere domínio a partir dos módulos alterados."""
    module_str = " ".join(modules).lower()
    if any(k in module_str for k in ["api", "http", "route", "controller"]):
        return "web_backend"
    if any(k in module_str for k in ["frontend", "react", "ui", "component"]):
        return "frontend_react"
    if any(k in module_str for k in ["pipeline", "etl", "data", "spark"]):
        return "data_pipeline"
    if any(k in module_str for k in ["cli", "cmd", "main"]):
        return "cli_tool"
    if any(k in module_str for k in ["lib", "shared", "util"]):
        return "library"
    return "generic"


def save_optimization(opt: DomainOptimization, path) -> None:
    with open(path, "w") as f:
        json.dump(opt.to_dict(), f, indent=2)
