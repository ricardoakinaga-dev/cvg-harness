"""
Research Agent
Explora o sistema e reduz cegueira técnica.
Gera research-notes.md e system-map.md.
P0/P1 - Componente do fluxo de pesquisa.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ResearchNote:
    """Resultado do research agent."""
    project: str
    feature: str
    fatos: list[str] = field(default_factory=list)
    hipoteses: list[str] = field(default_factory=list)
    riscos: list[str] = field(default_factory=list)
    restricoes: list[str] = field(default_factory=list)
    duvidas: list[str] = field(default_factory=list)
    modulos_impactados: list[str] = field(default_factory=list)
    dependencias_conhecidas: list[str] = field(default_factory=list)
    version: str = "v1"
    change_reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SystemMap:
    """Mapa do sistema."""
    project: str
    feature: str
    modulos: list[str] = field(default_factory=list)
    dependencias: list[str] = field(default_factory=list)
    zonas_criticas: list[str] = field(default_factory=list)
    arquivos_area: list[str] = field(default_factory=list)
    boundaries: list[str] = field(default_factory=list)
    version: str = "v1"
    change_reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class ResearchAgent:
    """
    Explora o codebase e gera research-notes.md e system-map.md.
    Regra: não confunde hipótese com fato.
    """

    MODULE_ALIASES = {
        "auth": {"auth", "oauth", "token", "login", "password", "security", "permission", "permissions", "permiss", "permissao", "permissoes", "authorization", "authorize", "role", "acl"},
        "api": {"api", "endpoint", "route", "rest", "http"},
        "database": {"database", "db", "migration", "schema", "sql"},
        "frontend": {"frontend", "ui", "component", "button", "page"},
        "release": {"release", "readiness", "deploy", "promotion", "deploying", "gate", "gates", "approva", "aprovacao", "promocao"},
        "gates": {"gate", "gates", "approval"},
        "metrics_agg": {"metric", "metrics", "metricas", "metrica", "metrico", "telemetry", "telemetria", "observability", "observabilidade"},
        "metrics": {"metric", "metrics", "metricas", "metrica", "telemetry", "telemetria", "observability", "observabilidade"},
        "spec_builder": {"spec", "builder", "specification"},
        "research": {"research", "discovery", "map"},
        "prd": {"prd", "product", "scope", "kpi"},
        "guardian": {"guard", "guardian", "architecture", "boundary"},
        "drift": {"drift", "alignment"},
        "sprint": {"sprint", "planner", "planning"},
        "classification": {"classification", "classifier", "intake"},
    }

    def investigate(
        self,
        project: str,
        feature: str,
        classification: dict,
        workspace: Optional[Path] = None,
    ) -> tuple[ResearchNote, SystemMap]:
        """
        Executa investigação e retorna notas e mapa do sistema.
        Usa sinais reais do workspace quando disponíveis e cai para heurística
        apenas quando o repositório não oferece evidência suficiente.
        """
        mode = classification.get("mode", "FAST")
        workspace_evidence = self._inspect_workspace(workspace)
        inferred_modules = self._infer_modules(feature, mode)
        observed_modules = self._match_feature_to_workspace_modules(
            feature,
            workspace_evidence["available_modules"],
        )
        modulos_impactados = self._merge_modules(
            observed_modules,
            inferred_modules,
        )
        arquivos_area = self._build_area_files(modulos_impactados, workspace_evidence)
        boundaries = self._infer_boundaries(workspace_evidence)
        zonas_criticas = self._infer_critical_areas(modulos_impactados, workspace_evidence)
        dependencias = self._infer_dependencies(modulos_impactados, workspace_evidence)

        facts = [
            f"Feature: {feature}",
            f"Modo: {mode}",
            f"Total score: {classification.get('total_score', 0)}",
        ]
        if workspace_evidence["workspace_root"]:
            facts.append(f"Workspace analisado: {workspace_evidence['workspace_root']}")
        if workspace_evidence["code_root"]:
            facts.append(f"Code root observado: {workspace_evidence['code_root']}")
        if workspace_evidence["available_modules"]:
            facts.append(
                "Módulos observados no codebase: "
                + ", ".join(workspace_evidence["available_modules"])
            )
        if observed_modules:
            facts.append(
                "Módulos com evidência local para a feature: "
                + ", ".join(observed_modules)
            )

        hypotheses = []
        if workspace and not observed_modules:
            hypotheses.append(
                "Módulos impactados derivados por heurística porque a árvore local não trouxe match direto suficiente"
            )
        elif not workspace_evidence["available_modules"]:
            hypotheses.append(
                "Investigação executada sem codebase observável; módulos derivados por heurística controlada"
            )

        risks = []
        if mode == "ENTERPRISE":
            risks.append("Impacto estrutural - requer validação extra")
        if any("auth" in m.lower() or "security" in m.lower() for m in modulos_impactados):
            risks.append("Área de segurança - risco de regressão alto")
        if any("api" in m.lower() for m in modulos_impactados):
            risks.append("Integração de API - contrato deve ser validado")
        if workspace and not observed_modules:
            risks.append("Workspace com sinal fraco para a feature - parte do research permanece heurística")

        research = ResearchNote(
            project=project,
            feature=feature,
            fatos=facts,
            hipoteses=hypotheses,
            riscos=risks,
            restricoes=["não alterar áreas não relacionadas ao escopo"],
            duvidas=["dependência externa está estável?"],
            modulos_impactados=modulos_impactados,
            dependencias_conhecidas=dependencias,
        )

        system_map = SystemMap(
            project=project,
            feature=feature,
            modulos=modulos_impactados,
            dependencias=dependencias,
            zonas_criticas=zonas_criticas,
            arquivos_area=arquivos_area,
            boundaries=boundaries,
        )

        return research, system_map

    def _infer_modules(self, feature: str, mode: str) -> list[str]:
        """Infere módulos impactados pela feature."""
        feature_lower = feature.lower()
        modules = []
        if any(k in feature_lower for k in ["auth", "login", "oauth", "token", "password", "permission", "permissions", "permiss", "permissao", "permissoes", "authorization", "authorize", "role", "acl"]):
            modules.append("auth")
        if any(k in feature_lower for k in ["api", "endpoint", "route", "rest"]):
            modules.append("api")
        if any(k in feature_lower for k in ["database", "db", "migration", "schema"]):
            modules.append("database")
        if any(k in feature_lower for k in ["release", "gates", "readiness", "deploy", "deployment", "approval", "aprovacao", "promocao"]):
            modules.append("release")
        if any(k in feature_lower for k in ["metric", "metricas", "metrica", "metrico", "telemetry", "telemetria", "observability", "observabilidade"]):
            modules.append("metrics")
        if any(k in feature_lower for k in ["frontend", "ui", "component", "button"]):
            modules.append("frontend")
        if not modules:
            modules = ["core"]
        return modules

    def _inspect_workspace(self, workspace: Optional[Path]) -> dict:
        """Coleta sinais reais do workspace para orientar o research."""
        evidence = {
            "workspace_root": None,
            "code_root": None,
            "code_prefix": None,
            "available_modules": [],
            "module_paths": {},
            "boundary_paths": [],
        }
        for root in self._candidate_workspace_roots(workspace):
            code_root, code_prefix = self._resolve_code_root(root)
            if not code_root:
                continue

            module_paths = {}
            available_modules = []
            for child in sorted(code_root.iterdir()):
                if not child.is_dir():
                    continue
                name = child.name
                if name.startswith(".") or name.startswith("__") or name.endswith(".egg-info"):
                    continue
                available_modules.append(name)
                module_paths[name] = f"{code_prefix}/{name}"

            boundary_paths = []
            for name in available_modules:
                lowered = name.lower()
                if any(token in lowered for token in ["legacy", "deprecated", "archive", "old", "v1"]):
                    boundary_paths.append(module_paths[name])

            if available_modules:
                evidence.update(
                    {
                        "workspace_root": str(root),
                        "code_root": code_prefix,
                        "code_prefix": code_prefix,
                        "available_modules": available_modules,
                        "module_paths": module_paths,
                        "boundary_paths": boundary_paths,
                    }
                )
                return evidence
        return evidence

    def _candidate_workspace_roots(self, workspace: Optional[Path]) -> list[Path]:
        roots = []
        if workspace:
            roots.append(Path(workspace))
        repo_root = Path(__file__).resolve().parents[3]
        if repo_root not in roots:
            roots.append(repo_root)
        return roots

    def _resolve_code_root(self, root: Path) -> tuple[Optional[Path], Optional[str]]:
        package_root = root / "src" / "cvg_harness"
        if package_root.exists():
            return package_root, "src/cvg_harness"

        src_root = root / "src"
        if src_root.exists():
            return src_root, "src"

        return None, None

    def _match_feature_to_workspace_modules(self, feature: str, available_modules: list[str]) -> list[str]:
        """Encontra módulos do workspace que combinam com a feature."""
        feature_tokens = self._tokenize(feature)
        matched = []
        for module in available_modules:
            module_tokens = self._tokenize(module)
            alias_tokens = self.MODULE_ALIASES.get(module, set())
            if feature_tokens & (module_tokens | alias_tokens):
                matched.append(module)
        return matched

    def _tokenize(self, text: str) -> set[str]:
        normalized = (
            unicodedata.normalize("NFKD", text.lower().replace("_", " ").replace("-", " "))
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        tokens = set(re.findall(r"[a-z0-9]+", normalized))
        normalized = set(tokens)
        for token in list(tokens):
            if token.endswith("s") and len(token) > 3:
                normalized.add(token[:-1])
        return normalized

    def _merge_modules(self, observed_modules: list[str], inferred_modules: list[str]) -> list[str]:
        """Combina módulos observados e inferidos preservando ordem."""
        merged = []
        for module in observed_modules + inferred_modules:
            if module not in merged:
                merged.append(module)
        return merged or ["core"]

    def _build_area_files(self, modules: list[str], workspace_evidence: dict) -> list[str]:
        """Deriva áreas/arquivos prováveis a partir dos módulos observados."""
        areas = []
        module_paths = workspace_evidence.get("module_paths", {})
        code_prefix = workspace_evidence.get("code_prefix") or "src"
        for module in modules:
            if module in module_paths:
                path = module_paths[module]
            else:
                path = f"{code_prefix}/{module}"
            areas.append(path.rstrip("/") + "/")
        return areas

    def _infer_boundaries(self, workspace_evidence: dict) -> list[str]:
        """Infere boundaries reais do workspace quando disponíveis."""
        boundaries = list(workspace_evidence.get("boundary_paths", []))
        defaults = ["src/legacy", "src/v1/deprecated"]
        for item in defaults:
            if item not in boundaries:
                boundaries.append(item)
        return boundaries

    def _infer_critical_areas(self, modules: list[str], workspace_evidence: Optional[dict] = None) -> list[str]:
        """Infere zonas críticas."""
        critical = []
        module_paths = workspace_evidence.get("module_paths", {}) if workspace_evidence else {}
        if "auth" in modules:
            critical.append("src/auth (autenticação)")
        if "api" in modules:
            critical.append("src/api (contratos de API)")
        if "release" in modules and "release" in module_paths:
            critical.append(f"{module_paths['release']} (prontidão e promoção)")
        if "gates" in modules and "gates" in module_paths:
            critical.append(f"{module_paths['gates']} (política formal de aprovação)")
        if workspace_evidence and workspace_evidence.get("boundary_paths"):
            for path in workspace_evidence["boundary_paths"]:
                critical.append(f"{path} (boundary sensível)")
        return critical

    def _infer_dependencies(self, modules: list[str], workspace_evidence: Optional[dict] = None) -> list[str]:
        """Infere dependências conhecidas."""
        deps = []
        if "auth" in modules:
            deps.append("database (tabela de usuários)")
        if "api" in modules:
            deps.append("auth (autenticação)")
        available = set(workspace_evidence.get("available_modules", [])) if workspace_evidence else set()
        if "release" in modules and "gates" in available:
            deps.append("gates (decisão formal de promoção)")
        if "release" in modules and "metrics_agg" in available:
            deps.append("metrics_agg (telemetria de prontidão)")
        if "drift" in modules and "evaluator" in available:
            deps.append("evaluator (evidências para detecção de drift)")
        return deps



def save_research(research: ResearchNote, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(research.to_dict(), f, indent=2)



def save_system_map(system_map: SystemMap, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(system_map.to_dict(), f, indent=2)



def load_research(path: Path) -> ResearchNote:
    with open(path) as f:
        return ResearchNote(**json.load(f))



def load_system_map(path: Path) -> SystemMap:
    with open(path) as f:
        return SystemMap(**json.load(f))



def render_research_notes_markdown(research: ResearchNote) -> str:
    """Gera research-notes.md legível."""
    lines = [
        "# Research Notes",
        "",
        f"**Projeto:** {research.project}",
        f"**Feature:** {research.feature}",
        f"**Data:** {research.created_at}",
        "",
        "## Facts",
        "",
    ]
    for fato in research.fatos:
        lines.append(f"- {fato}")
    lines.extend(["", "## Hipóteses", ""])
    for hip in research.hipoteses:
        lines.append(f"- {hip}")
    lines.extend(["", "## Riscos", ""])
    for risco in research.riscos:
        lines.append(f"- {risco}")
    lines.extend(["", "## Restrições", ""])
    for restr in research.restricoes:
        lines.append(f"- {restr}")
    lines.extend(["", "## Dúvidas", ""])
    for duvida in research.duvidas:
        lines.append(f"- {duvida}")
    lines.extend(["", "## Módulos Impactados", ""])
    for mod in research.modulos_impactados:
        lines.append(f"- {mod}")
    lines.extend(["", "## Dependências Conhecidas", ""])
    for dep in research.dependencias_conhecidas:
        lines.append(f"- {dep}")
    return "\n".join(lines)



def render_system_map_markdown(system_map: SystemMap) -> str:
    """Gera system-map.md legível."""
    lines = [
        "# System Map",
        "",
        f"**Projeto:** {system_map.project}",
        f"**Feature:** {system_map.feature}",
        f"**Data:** {system_map.created_at}",
        "",
        "## Módulos",
        "",
    ]
    for mod in system_map.modulos:
        lines.append(f"- {mod}")
    lines.extend(["", "## Dependências", ""])
    for dep in system_map.dependencias:
        lines.append(f"- {dep}")
    lines.extend(["", "## Zonas Críticas", ""])
    for zona in system_map.zonas_criticas:
        lines.append(f"- {zona}")
    lines.extend(["", "## Arquivos/Áreas", ""])
    for arq in system_map.arquivos_area:
        lines.append(f"- {arq}")
    lines.extend(["", "## Boundaries", ""])
    for bound in system_map.boundaries:
        lines.append(f"- {bound}")
    return "\n".join(lines)



def save_research_markdown(research: ResearchNote, output_path: Path) -> None:
    """Salva research-notes.md."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(render_research_notes_markdown(research))



def save_system_map_markdown(system_map: SystemMap, output_path: Path) -> None:
    """Salva system-map.md."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(render_system_map_markdown(system_map))
