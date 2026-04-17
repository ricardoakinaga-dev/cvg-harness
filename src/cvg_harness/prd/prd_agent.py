"""
PRD Agent
Formaliza o problema de produto e os limites de negócio.
Gera prd.md.
P0/P1 - Componente do fluxo de produto.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class PRD:
    """Documento de PRD."""
    project: str
    feature: str
    problema: str
    objetivo: str
    kpis: list[str] = field(default_factory=list)
    escopo: list[str] = field(default_factory=list)
    fora_de_escopo: list[str] = field(default_factory=list)
    user_stories: list[str] = field(default_factory=list)
    riscos: list[str] = field(default_factory=list)
    criterios_aceite: list[str] = field(default_factory=list)
    version: str = "v1"
    change_reason: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class PRDAgent:
    """
    Converte necessidade em definição de problema, objetivo, escopo e sucesso.
    Regras: não assumir que o problema já está resolvido.
    """

    def create_prd(
        self,
        project: str,
        feature: str,
        research_notes: dict,
        classification: dict,
        context: Optional[dict] = None,
    ) -> PRD:
        """
        Cria PRD a partir de research e classificação.
        """
        research_modules = research_notes.get("modulos_impactados", [])
        risks = self._identify_risks(classification, research_notes)
        problem = self._define_problem(feature, research_notes, research_modules, risks)
        objective = self._define_objective(feature, classification, research_notes, research_modules, risks)
        in_scope, out_scope = self._define_scope(feature, classification, research_notes, research_modules)
        kpis = self._suggest_kpis(feature, research_notes, classification, research_modules)
        user_stories = self._suggest_user_stories(feature, research_notes, in_scope, research_modules)
        acceptance = self._suggest_acceptance_criteria(
            feature,
            in_scope,
            research_notes,
            classification,
            research_modules,
            risks,
        )

        return PRD(
            project=project,
            feature=feature,
            problema=problem,
            objetivo=objective,
            kpis=kpis,
            escopo=in_scope,
            fora_de_escopo=out_scope,
            user_stories=user_stories,
            riscos=risks,
            criterios_aceite=acceptance,
        )

    def _define_problem(
        self,
        feature: str,
        research: dict,
        modules: list[str],
        risks: list[str],
    ) -> str:
        """Define o problema a resolver com base no research."""
        module_text = self._format_modules(modules)
        top_risk = risks[0] if risks else "sem risco dominante explícito"
        top_restriction = self._first_meaningful(research.get("restricoes", []))
        observed_fact = self._first_meaningful(research.get("fatos", []))

        parts = [f"{feature} precisa ser entregue com segurança em {module_text}"]
        if observed_fact:
            parts.append(f"Contexto observado: {observed_fact}")
        if top_risk:
            parts.append(f"Risco dominante: {top_risk}")
        if top_restriction:
            parts.append(f"Restrição operacional: {top_restriction}")
        return ". ".join(parts)

    def _define_objective(
        self,
        feature: str,
        classification: dict,
        research: dict,
        modules: list[str],
        risks: list[str],
    ) -> str:
        """Define o objetivo mensurável a partir do research real."""
        mode = classification.get("mode", "FAST")
        module_text = self._format_modules(modules)
        restriction = self._first_meaningful(research.get("restricoes", []))
        risk = risks[0] if risks else None

        objective = f"Entregar {feature} em {module_text} com comportamento observável e escopo controlado"
        if mode == "ENTERPRISE":
            objective += ", preservando contratos críticos e validando regressão antes de promoção"
        if restriction:
            objective += f". Respeitar explicitamente: {restriction}"
        if risk:
            objective += f". Reduzir o risco principal: {risk}"
        return objective

    def _suggest_kpis(
        self,
        feature: str,
        research: dict,
        classification: dict,
        modules: list[str],
    ) -> list[str]:
        """Sugere KPIs baseados na feature, módulos e modo operacional."""
        kpis = []
        mode = classification.get("mode", "FAST")

        if "release" in modules or "gates" in modules:
            kpis.extend([
                "Decisão de prontidão gerada sem gate obrigatório ausente",
                "Evidência de `release-readiness-report.json` consistente com gates persistidos",
            ])
        if "api" in modules:
            kpis.extend([
                "Contrato de API validado para os endpoints impactados",
                "Sem quebra de compatibilidade com consumidor conhecido",
            ])
        if "auth" in modules:
            kpis.extend([
                "Fluxo de autenticação crítico validado sem regressão funcional",
                "Cenários de sessão expirada e credenciais inválidas cobertos",
            ])
        if "metrics" in modules or "metrics_agg" in modules:
            kpis.append("Telemetria do caminho alterado refletida em eventos e métricas")

        restriction = self._first_meaningful(research.get("restricoes", []))
        if restriction:
            kpis.append(f"Restrição operacional preservada: {restriction}")

        if mode == "ENTERPRISE":
            kpis.append("Validação de regressão concluída para o escopo crítico")

        if not kpis:
            kpis.extend([
                f"{feature} implementado com escopo validado",
                "Code review sem bloqueadores",
                "Testes do fluxo alterado passando",
            ])

        return self._deduplicate(kpis)

    def _define_scope(
        self,
        feature: str,
        classification: dict,
        research: dict,
        modules: list[str],
    ) -> tuple[list[str], list[str]]:
        """Define escopo dentro e fora com base no research real."""
        mode = classification.get("mode", "FAST")
        in_scope = [f"Implementar {feature} no escopo dos módulos {self._format_modules(modules)}"]
        out_scope = ["Mudanças não relacionadas à feature"]

        if "release" in modules or "gates" in modules:
            in_scope.append("Regras de promoção e rastreio de readiness")
            in_scope.append("Alinhar regras de promoção, gates obrigatórios e rastreabilidade de readiness")
            out_scope.append("Alterar política de promoção fora dos gates impactados")
        if "auth" in modules:
            in_scope.append("Validar autenticação, autorização e cenários de sessão crítica")
            out_scope.append("Redesenhar identidade/SSO fora do fluxo impactado")
        if "api" in modules:
            in_scope.append("Validar contratos, payloads e compatibilidade dos endpoints afetados")
            out_scope.append("Versionar endpoints não citados no research")
        if "metrics" in modules or "metrics_agg" in modules:
            in_scope.append("Manter telemetria e leitura operacional coerentes para o caminho alterado")
            out_scope.append("Reescrever pipeline analítico fora do trajeto afetado")

        for restriction in research.get("restricoes", [])[:2]:
            in_scope.append(f"Preservar restrição do research: {restriction}")

        if mode == "ENTERPRISE":
            in_scope.append("Validação de contrato de API")
            in_scope.append("Testes de regressão")
            in_scope.append("Executar validação de regressão para os módulos críticos")
            out_scope.append("Refatoração estrutural sem relação com o objetivo do PRD")

        return self._deduplicate(in_scope), self._deduplicate(out_scope)

    def _identify_risks(self, classification: dict, research: dict) -> list[str]:
        """Identifica riscos a partir de research, restrições e modo."""
        risks = []
        mode = classification.get("mode", "FAST")

        for risk in research.get("riscos", []):
            if risk not in risks:
                risks.append(risk)

        for restriction in research.get("restricoes", [])[:2]:
            normalized = f"Restrição operacional a preservar: {restriction}"
            if normalized not in risks:
                risks.append(normalized)

        modules = set(research.get("modulos_impactados", []))
        if "metrics" in modules or "metrics_agg" in modules:
            risks.append("Medições e dados observáveis devem preservar granularidade útil")
        if "release" in modules or "gates" in modules:
            risks.append("Mudança em gates/readiness pode bloquear promoção se ficar inconsistente")
        if "auth" in modules:
            risks.append("Regressão em autenticação pode bloquear jornadas críticas")
        if mode == "ENTERPRISE":
            risks.append("Alto risco de regressão em múltiplos módulos")

        return self._deduplicate(risks)

    def _suggest_user_stories(
        self,
        feature: str,
        research: dict,
        in_scope: list[str],
        modules: list[str],
    ) -> list[str]:
        """Sugere user stories com base no impacto real do research."""
        feature_lower = feature.lower()
        stories = [f"Como usuário, quero {feature_lower} sem regressão no fluxo principal"]

        if "auth" in modules:
            stories.append("Como usuário autenticado, quero manter sessão e autorização consistentes após a mudança")
        if "api" in modules:
            stories.append("Como integrador, quero consumir os endpoints impactados com contratos estáveis")
        if "release" in modules or "gates" in modules:
            stories.append("Como operador, quero evidência clara de gates e release readiness para decidir promoção")
        if "metrics" in modules or "metrics_agg" in modules:
            stories.append("Como SRE, quero telemetria coerente do fluxo alterado para detectar regressões")

        question = self._first_meaningful(research.get("duvidas", []))
        if question:
            stories.append(f"Como responsável técnico, quero fechar a dúvida crítica: {question}")

        if len(stories) < 2:
            stories.append(f"Como sistema, preciso que {feature_lower} respeite o escopo definido no PRD")
        return self._deduplicate(stories)

    def _suggest_acceptance_criteria(
        self,
        feature: str,
        in_scope: list[str],
        research: dict,
        classification: dict,
        modules: list[str],
        risks: list[str],
    ) -> list[str]:
        """Sugere critérios de aceite derivados do research real."""
        criteria = [
            f"{feature} funciona corretamente no escopo definido do PRD",
            f"Escopo principal respeitado: {in_scope[0]}",
        ]

        if "auth" in modules:
            criteria.append("Cenários críticos de autenticação e sessão passam sem regressão")
        if "api" in modules:
            criteria.append("Contratos dos endpoints impactados permanecem válidos")
        if "release" in modules or "gates" in modules:
            criteria.append("Gates e evidência de readiness permanecem coerentes após a mudança")
        if "metrics" in modules or "metrics_agg" in modules:
            criteria.append("Eventos e métricas do fluxo alterado permanecem observáveis")

        for restriction in research.get("restricoes", [])[:2]:
            criteria.append(f"Restrição preservada: {restriction}")

        top_risk = risks[0] if risks else None
        if top_risk:
            criteria.append(f"Risco principal mitigado ou coberto por evidência: {top_risk}")

        if classification.get("mode", "FAST") == "ENTERPRISE":
            criteria.append("Validação de regressão concluída para os módulos críticos")

        criteria.append("Code review aprovado")
        criteria.append("Testes passando")
        return self._deduplicate(criteria)

    def _format_modules(self, modules: list[str]) -> str:
        if not modules:
            return "módulos centrais do fluxo"
        return ", ".join(modules)

    def _first_meaningful(self, items: list[str]) -> str | None:
        for item in items:
            if item and str(item).strip():
                return str(item).strip()
        return None

    def _deduplicate(self, items: list[str]) -> list[str]:
        ordered = []
        for item in items:
            if item not in ordered:
                ordered.append(item)
        return ordered



def save_prd(prd: PRD, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(prd.to_dict(), f, indent=2)



def load_prd(path: Path) -> PRD:
    with open(path) as f:
        return PRD(**json.load(f))



def render_prd_markdown(prd: PRD) -> str:
    """Gera prd.md legível."""
    lines = [
        "# PRD: " + prd.feature,
        "",
        f"**Projeto:** {prd.project}",
        f"**Feature:** {prd.feature}",
        f"**Data:** {prd.created_at}",
        "",
        "## Problema",
        "",
        prd.problema,
        "",
        "## Objetivo",
        "",
        prd.objetivo,
        "",
        "## KPIs",
        "",
    ]
    for kpi in prd.kpis:
        lines.append(f"- {kpi}")
    lines.extend(["", "## Escopo", "", "### Dentro do escopo", ""])
    for item in prd.escopo:
        lines.append(f"- {item}")
    lines.extend(["", "### Fora do escopo", ""])
    for item in prd.fora_de_escopo:
        lines.append(f"- {item}")
    lines.extend(["", "## User Stories", ""])
    for story in prd.user_stories:
        lines.append(f"- {story}")
    lines.extend(["", "## Riscos", ""])
    for risco in prd.riscos:
        lines.append(f"- {risco}")
    lines.extend(["", "## Critérios de Aceite", ""])
    for criterio in prd.criterios_aceite:
        lines.append(f"- {criterio}")
    return "\n".join(lines)



def save_prd_markdown(prd: PRD, output_path: Path) -> None:
    """Salva prd.md."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(render_prd_markdown(prd))
