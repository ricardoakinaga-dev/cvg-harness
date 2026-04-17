"""
Spec Builder Agent
Traduz PRD e research em especificação técnica executável.
Gera spec.md e spec.json.
P0/P1 - Componente do fluxo de especificação.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class Spec:
    """SPEC determinística para agentes e orquestração."""
    meta: str
    modulos: list[str]
    areas_autorizadas: list[str] = field(default_factory=list)
    areas_proibidas: list[str] = field(default_factory=list)
    contratos: list[dict] = field(default_factory=list)
    sprints: list[str] = field(default_factory=list)
    criterios: list[dict] = field(default_factory=list)
    edge_cases: list[str] = field(default_factory=list)
    observabilidade: str = ""
    rollback: str = ""
    limite_escopo: str = ""
    fluxo_critico: bool = False
    mudanca_estrutural: bool = False
    version: str = "v1"
    change_reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class SpecBuilderAgent:
    """
    Gera SPEC determinística a partir de PRD e research.
    Regra: não deixa critério não testável sem marcar como lacuna.
    """

    def build(
        self,
        prd: dict,
        research_notes: dict,
        classification: dict,
    ) -> Spec:
        """
        Constrói SPEC a partir de PRD e research.
        """
        mode = classification.get("mode", "FAST")
        meta = prd.get("objetivo", "implementar feature")
        modulos = research_notes.get("modulos_impactados", ["core"])
        areas_autorizadas = research_notes.get("arquivos_area", [f"src/{m}/" for m in modulos])
        zonas_criticas = research_notes.get("zonas_criticas", [])
        boundaries = research_notes.get("boundaries", ["src/legacy", "src/v1/deprecated"])
        contratos = self._build_contracts(prd, research_notes, modulos)

        spec = Spec(
            meta=meta,
            modulos=modulos,
            areas_autorizadas=areas_autorizadas,
            areas_proibidas=boundaries,
            contratos=contratos,
            edge_cases=self._suggest_edge_cases(modulos),
            criterios=self._build_criteria(prd, mode, modulos, research_notes),
            observabilidade=self._suggest_observability(modulos),
            rollback=self._suggest_rollback(modulos),
            limite_escopo=", ".join(prd.get("escopo", [])),
            fluxo_critico=mode == "ENTERPRISE",
            mudanca_estrutural=mode == "ENTERPRISE",
            version="v1",
        )

        return spec

    def _build_criteria(self, prd: dict, mode: str, modulos: list[str], research_notes: dict) -> list[dict]:
        """Constrói critérios de aceite."""
        criterios = []
        for criterio in prd.get("criterios_aceite", []):
            criterio_norm = self._normalize_criterion(criterio)
            criterios.append({
                "descricao": criterio_norm["descricao"],
                "testavel": criterio_norm["testavel"],
                "definido_como_lacuna": criterio_norm["definido_como_lacuna"],
            })
        if not criterios:
            criterios.append({
                "descricao": "Feature implementada e testada em ambiente real",
                "testavel": True,
                "definido_como_lacuna": False,
            })
        if modulos and "api" in modulos and not any("payload" in str(c).lower() for c in prd.get("criterios_aceite", [])):
            criterios.append({
                "descricao": "Definir e validar payloads/contratos por endpoint em testes integrados",
                "testavel": False,
                "definido_como_lacuna": True,
            })
        if mode == "ENTERPRISE":
            criterios.append({
                "descricao": "Code review aprovado",
                "testavel": True,
                "definido_como_lacuna": False,
            })
            criterios.append({
                "descricao": "Testes passando",
                "testavel": True,
                "definido_como_lacuna": False,
            })
            if "auth" in modulos:
                criterios.append({
                    "descricao": "Plano de rollback de sessão autenticada atualizado após aprovação",
                    "testavel": False,
                    "definido_como_lacuna": True,
                })
        return criterios

    def _normalize_criterion(self, texto: str) -> dict[str, object]:
        texto_limpo = (texto or "").strip()
        if not texto_limpo:
            return {
                "descricao": "Critério não especificado no PRD",
                "testavel": False,
                "definido_como_lacuna": True,
            }

        texto_min = texto_limpo.lower()
        if any(mark in texto_min for mark in ("implementada e funcionando", "implementada e func", "funcionando")):
            return {
                "descricao": texto_limpo,
                "testavel": False,
                "definido_como_lacuna": True,
            }

        if len(texto_limpo) < 22:
            return {
                "descricao": texto_limpo,
                "testavel": False,
                "definido_como_lacuna": True,
            }

        return {
            "descricao": texto_limpo,
            "testavel": True,
            "definido_como_lacuna": False,
        }

    def _build_contracts(self, prd: dict, research_notes: dict, modulos: list[str]) -> list[dict]:
        """Cria contratos executáveis mínimos e alinhados ao contexto detectado."""
        contratos = []
        objetivo = (prd.get("objetivo", "") or "").lower()

        recurso = self._infer_resource_name(objetivo, modulos)
        if "api" in modulos or "api" in objetivo:
            contratos.append({
                "nome": f"{recurso}_create",
                "tipo": "integracao",
                "criticidade": "high",
                "superficie": "api",
                "metodo": "POST",
                "path": f"/api/{recurso}",
                "evidencia_minima": ["payload de criação", "resposta 2xx", "persistência observável"],
                "exemplo_payload": {"action": "create", recurso: {"id": "uuid", "nome": "string"}},
                "descricao": f"Contrato de criação para {recurso} com payload explícito para validação",
            })
            contratos.append({
                "nome": f"{recurso}_get",
                "tipo": "integracao",
                "criticidade": "medium",
                "superficie": "api",
                "metodo": "GET",
                "path": f"/api/{recurso}/{{id}}",
                "evidencia_minima": ["status 200/404", "serialização estável"],
                "descricao": f"Contrato de consulta para {recurso}",
            })

        if "auth" in modulos:
            contratos.append({
                "nome": "auth_session",
                "tipo": "auth",
                "criticidade": "high",
                "superficie": "auth",
                "fluxo": "login|refresh|logout",
                "evidencia_minima": ["login bem-sucedido", "falha de credencial", "sessao rastreada"],
                "descricao": "Contrato de sessão autenticada para escopo de feature.",
            })

        if "database" in modulos:
            contratos.append({
                "nome": "database_write",
                "tipo": "storage",
                "criticidade": "high",
                "superficie": "database",
                "evidencia_minima": ["write persistido", "rollback validado", "migração rastreável"],
                "descricao": "Contrato de persistência para registros críticos alterados pela feature",
            })

        if "release" in modulos or "gates" in modulos:
            contratos.append({
                "nome": "release_readiness_payload",
                "tipo": "processo",
                "criticidade": "high",
                "superficie": "release",
                "evidencia_minima": ["gates summary", "missing gates", "residual risks"],
                "descricao": "Contrato de input para decisão de readiness e status de gates",
            })

        if not contratos and research_notes.get("arquivos_area"):
            contratos.append({
                "nome": "area_change_contract",
                "tipo": "implementation_scope",
                "criticidade": "low",
                "superficie": "scope",
                "evidencia_minima": research_notes.get("arquivos_area", []),
                "descricao": "Contrato de implementação restrito às áreas mapeadas em arquivos_area",
                "areas_autorizadas": research_notes.get("arquivos_area", []),
            })

        return contratos

    def _contract_metadata(self, criticidade: str, superficie: str, evidencia_minima: list[str]) -> dict:
        """Campos curtos para priorizar contratos por risco e superfície."""
        return {
            "criticidade": criticidade,
            "superficie": superficie,
            "evidencia_minima": evidencia_minima,
        }

    def _infer_resource_name(self, objetivo: str, modulos: list[str]) -> str:
        """Inferência simples de recurso para contratos API."""
        candidatos = [
            "auth",
            "release",
            "gateway",
            "usuario",
            "user",
            "item",
            "order",
            "pedido",
            "metric",
            "event",
        ]
        for candidato in candidatos:
            if candidato in objetivo:
                return candidato.replace("usuario", "usuario")
        if modulos:
            return modulos[0]
        return "feature"

    def _suggest_edge_cases(self, modulos: list[str]) -> list[str]:
        """Sugere edge cases baseados nos módulos."""
        edge_cases = ["erro de conexão", "timeout"]
        if "auth" in modulos:
            edge_cases.extend(["token expirado", "credenciais inválidas"])
        if "api" in modulos:
            edge_cases.extend(["payload inválido", "rate limit"])
        return edge_cases

    def _suggest_observability(self, modulos: list[str]) -> str:
        """Sugere observabilidade."""
        parts = []
        if "auth" in modulos:
            parts.append("logs estruturados de auth, correlação de sessão e métricas de login/logout")
        if "api" in modulos:
            parts.append("logs de request/response, status code e latência p95")
        if "release" in modulos or "gates" in modulos:
            parts.append("logs de decisão de readiness, resumo de gates e bloqueadores")
        if "database" in modulos:
            parts.append("logs de persistência, migração e rollback observável")
        if parts:
            return "; ".join(parts)
        return "logs básicos"

    def _suggest_rollback(self, modulos: list[str]) -> str:
        """Sugere procedimento de rollback."""
        if "database" in modulos:
            return "reverter migração, validar snapshot e repetir leitura dos dados críticos"
        if "release" in modulos or "gates" in modulos:
            return "reabrir readiness, reverter decisão de promoção e registrar bloqueador"
        if "auth" in modulos and "api" in modulos:
            return "reverter endpoint e invalidar sessões ativas"
        if "auth" in modulos:
            return "reverter auth e limpar sessões ativas"
        if "api" in modulos:
            return "reverter handler/endpoints e revisar contrato exposto"
        return "git revert do commit"


def save_spec(spec: Spec, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(spec.to_dict(), f, indent=2)


def load_spec(path: Path) -> Spec:
    with open(path) as f:
        return Spec(**json.load(f))


def render_spec_markdown(spec: Spec) -> str:
    """Gera spec.md legível."""
    lines = [
        "# SPEC: " + spec.meta,
        "",
        f"**Versão:** {spec.version}",
        f"**Módulos:** {', '.join(spec.modulos)}",
        f"**Data:** {spec.created_at}",
        "",
        "## Meta",
        "",
        spec.meta,
        "",
        "## Módulos Afetados",
        "",
    ]
    for mod in spec.modulos:
        lines.append(f"- {mod}")
    lines.extend(["", "## Áreas Autorizadas", ""])
    for area in spec.areas_autorizadas:
        lines.append(f"- {area}")
    lines.extend(["", "## Áreas Proibidas", ""])
    for area in spec.areas_proibidas:
        lines.append(f"- {area}")
    if spec.contratos:
        lines.extend(["", "## Contratos", ""])
        for contrato in spec.contratos:
            lines.append(f"- {contrato}")
    if spec.criterios:
        lines.extend(["", "## Critérios de Aceite", ""])
        lines.append("| Critério | Testável | Lacuna |")
        lines.append("|----------|----------|--------|")
        for c in spec.criterios:
            testavel = "sim" if c.get("testavel") else "não"
            lacuna = "sim" if c.get("definido_como_lacuna") else "não"
            lines.append(f"| {c.get('descricao', '')} | {testavel} | {lacuna} |")
    if spec.edge_cases:
        lines.extend(["", "## Edge Cases", ""])
        for ec in spec.edge_cases:
            lines.append(f"- {ec}")
    if spec.observabilidade:
        lines.extend(["", "## Observabilidade", "", spec.observabilidade])
    if spec.rollback:
        lines.extend(["", "## Rollback", "", spec.rollback])
    if spec.limite_escopo:
        lines.extend(["", "## Limite de Escopo", "", spec.limite_escopo])
    return "\n".join(lines)


def save_spec_markdown(spec: Spec, output_path: Path) -> None:
    """Salva spec.md."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(render_spec_markdown(spec))


def save_spec_pair(spec: Spec, json_path: Path, md_path: Path) -> None:
    """Salva spec.json e spec.md com versão sincronizada."""
    spec_json = spec.to_dict()
    spec_json["version"] = spec.version
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(spec_json, f, indent=2)
    save_spec_markdown(spec, md_path)
