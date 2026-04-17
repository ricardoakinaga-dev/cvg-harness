"""
P0-2: Contratos dos artefatos
Define contratos fortes com áreas autorizadas e proibidas para spec.json.
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
class ArtifactContract:
    """Contrato base para todos os artefatos."""
    name: str
    objective: str
    generated_by: str
    created_at_trigger: str
    mutable_until_gate: str
    approved_by: str
    required_fields: list[str]
    neighboring_artifacts: list[str]
    version: str = "v1"
    change_reason: Optional[str] = None


@dataclass
class SpecContract(ArtifactContract):
    """Contrato estendido para spec.json."""
    authorized_areas: list[str] = field(default_factory=list)
    prohibited_areas: list[str] = field(default_factory=list)
    handoff_minimum: str = ""
    min_sprints: int = 1


ARTIFACT_CONTRACTS = {
    "intake.md": ArtifactContract(
        name="intake.md",
        objective="registrar a demanda inicial",
        generated_by="Intake Classifier",
        created_at_trigger="recebimento da demanda",
        mutable_until_gate="GATE_0",
        approved_by="owner da demanda",
        required_fields=["problema", "contexto", "urgencia", "impacto", "premissas", "perguntas"],
        neighboring_artifacts=["classification.json"],
    ),
    "classification.json": ArtifactContract(
        name="classification.json",
        objective="classificar complexidade e modo",
        generated_by="Intake Classifier",
        created_at_trigger="após intake",
        mutable_until_gate="reclassificação formal",
        approved_by="planner responsável",
        required_fields=["project", "demand", "mode", "total_score", "dimensions", "rationale", "override_applied", "classified_by", "timestamp"],
        neighboring_artifacts=["intake.md"],
    ),
    "research-notes.md": ArtifactContract(
        name="research-notes.md",
        objective="consolidar fatos técnicos, riscos e restrições",
        generated_by="Research Agent",
        created_at_trigger="após classificação",
        mutable_until_gate="GATE_1",
        approved_by="planner técnico",
        required_fields=["project", "feature", "fatos", "hipoteses", "riscos", "restricoes", "duvidas", "modulos_impactados", "dependencias_conhecidas", "version", "created_at"],
        neighboring_artifacts=["system-map.md", "classification.json"],
    ),
    "system-map.md": ArtifactContract(
        name="system-map.md",
        objective="mapear módulos, boundaries e superfícies afetadas",
        generated_by="Research Agent",
        created_at_trigger="durante research",
        mutable_until_gate="GATE_1",
        approved_by="planner técnico",
        required_fields=["project", "feature", "modulos", "dependencias", "zonas_criticas", "arquivos_area", "boundaries", "version", "created_at"],
        neighboring_artifacts=["research-notes.md"],
    ),
    "prd.md": ArtifactContract(
        name="prd.md",
        objective="definir problema, objetivo, sucesso e limites de negócio",
        generated_by="PRD Agent",
        created_at_trigger="após research",
        mutable_until_gate="GATE_2 ou replan formal",
        approved_by="owner de produto",
        required_fields=["project", "feature", "problema", "objetivo", "kpis", "escopo", "fora_de_escopo", "user_stories", "riscos", "criterios_aceite", "version", "created_at"],
        neighboring_artifacts=["research-notes.md", "classification.json"],
    ),
    "spec.md": ArtifactContract(
        name="spec.md",
        objective="especificação legível para humanos",
        generated_by="Spec Builder",
        created_at_trigger="após PRD",
        mutable_until_gate="GATE_3 ou replan formal",
        approved_by="planner técnico",
        required_fields=["objetivo_tecnico", "modulos_afetados", "regras", "fluxos", "erros", "limites", "testes"],
        neighboring_artifacts=["spec.json", "prd.md", "research-notes.md"],
    ),
    "spec.json": SpecContract(
        name="spec.json",
        objective="especificação determinística para agentes e orquestração",
        generated_by="Spec Builder",
        created_at_trigger="junto com spec.md",
        mutable_until_gate="em sincronia com spec.md",
        approved_by="planner técnico",
        required_fields=["meta", "modulos", "areas_autorizadas", "areas_proibidas", "contratos", "sprints", "criterios", "edge_cases", "observabilidade", "rollback"],
        neighboring_artifacts=["spec.md", "prd.md"],
        authorized_areas=[],
        prohibited_areas=[],
        handoff_minimum="",
        min_sprints=1,
    ),
    "spec-lint-report.json": ArtifactContract(
        name="spec-lint-report.json",
        objective="registrar qualidade executável da SPEC",
        generated_by="Spec Linter",
        created_at_trigger="após SPEC",
        mutable_until_gate="a cada rerun do lint",
        approved_by="automático + revisão humana quando bloqueante",
        required_fields=["resultado", "falhas", "warnings", "score", "recomendacao"],
        neighboring_artifacts=["spec.json", "spec.md"],
    ),
    "sprint-plan.json": ArtifactContract(
        name="sprint-plan.json",
        objective="quebrar a SPEC em sprints fechadas",
        generated_by="Sprint Planner",
        created_at_trigger="após lint aprovado",
        mutable_until_gate="replan formal",
        approved_by="planner técnico",
        required_fields=["sprints", "dependencias", "agente_alvo", "criterios", "evidencias", "risco"],
        neighboring_artifacts=["execution-order.json", "spec.json"],
    ),
    "execution-order.json": ArtifactContract(
        name="execution-order.json",
        objective="definir ordem de promoção e pré-condições",
        generated_by="Sprint Planner / Orchestrator",
        created_at_trigger="após sprint plan",
        mutable_until_gate="replan formal",
        approved_by="orchestrator owner",
        required_fields=["sequencia", "bloqueios", "paralelismo_permitido", "pre_conds"],
        neighboring_artifacts=["sprint-plan.json", "progress.json"],
    ),
    "architecture-guard-report.json": ArtifactContract(
        name="architecture-guard-report.json",
        objective="registrar aderência arquitetural da sprint",
        generated_by="Architecture Guardian",
        created_at_trigger="durante/ao final da sprint",
        mutable_until_gate="a cada revalidação",
        approved_by="architecture owner ou waiver formal",
        required_fields=["resultado", "desvios", "severidade", "areas_afetadas", "decisao"],
        neighboring_artifacts=["spec.json", "sprint-plan.json"],
    ),
    "evaluation-report.json": ArtifactContract(
        name="evaluation-report.json",
        objective="registrar resultado da validação funcional/técnica",
        generated_by="Evaluator",
        created_at_trigger="após entrega da sprint",
        mutable_until_gate="a cada novo round",
        approved_by="evaluator lead",
        required_fields=[
            "sprint_id",
            "spec_ref",
            "result",
            "criterion_results",
            "criterios",
            "status",
            "evidencias",
            "falhas",
            "evidence_provided",
            "evidence_missing",
            "structured_evidence_count",
            "structured_evidence_summary",
            "next_action",
            "round",
            "timestamp",
        ],
        neighboring_artifacts=["spec.json", "sprint-plan.json", "architecture-guard-report.json"],
    ),
    "drift-report.json": ArtifactContract(
        name="drift-report.json",
        objective="medir desalinhamento entre artefatos e execução",
        generated_by="Drift Detector",
        created_at_trigger="após avaliação ou antes de release",
        mutable_until_gate="a cada rodada de detecção",
        approved_by="planner técnico",
        required_fields=["drift_por_camada", "severidade", "causa_probavel", "acao_requerida"],
        neighboring_artifacts=["spec.json", "prd.md", "intake.md"],
    ),
    "progress.json": ArtifactContract(
        name="progress.json",
        objective="estado vivo da execução",
        generated_by="Orchestrator",
        created_at_trigger="ao abrir o fluxo",
        mutable_until_gate="durante toda a execução",
        approved_by="sistema/orchestrator",
        required_fields=["modo", "sprint_atual", "status", "rounds", "bloqueios", "metricas", "aprovacoes"],
        neighboring_artifacts=["event-log.jsonl"],
    ),
    "event-log.jsonl": ArtifactContract(
        name="event-log.jsonl",
        objective="trilha imutável de eventos",
        generated_by="Orchestrator e motores de gate",
        created_at_trigger="no início do fluxo",
        mutable_until_gate="apenas append",
        approved_by="não se aplica",
        required_fields=["timestamp", "event_type", "actor", "artifact_ref", "metadata"],
        neighboring_artifacts=["progress.json"],
    ),
    "release-readiness-report.json": ArtifactContract(
        name="release-readiness-report.json",
        objective="consolidar decisão final de prontidão (artefato canônico)",
        generated_by="Release Readiness Engine",
        created_at_trigger="ao fim das sprints",
        mutable_until_gate="GATE_9",
        approved_by="owner técnico e owner de release",
        required_fields=["project", "feature", "decision", "gates_summary", "missing_gates", "exceptions", "residual_risks", "waivers", "timestamp"],
        neighboring_artifacts=["evaluation-report.json", "drift-report.json", "progress.json", "release-readiness.md"],
    ),
    "release-readiness.md": ArtifactContract(
        name="release-readiness.md",
        objective="versão legível para humanos do release readiness (sidecar opcional)",
        generated_by="Release Readiness Engine",
        created_at_trigger="ao fim das sprints (opcional)",
        mutable_until_gate="GATE_9",
        approved_by="owner técnico e owner de release",
        required_fields=["resumo", "gates", "excecoes", "riscos_residuais", "decisao"],
        neighboring_artifacts=["release-readiness-report.json"],
    ),
    "external-dispatch-plan.json": ArtifactContract(
        name="external-dispatch-plan.json",
        objective="registrar o plano formal de dispatch externo opt-in",
        generated_by="Operator Service + ExternalExecutorBridge",
        created_at_trigger="quando o operador prepara handoff para executor externo",
        mutable_until_gate="a cada novo dispatch planejado",
        approved_by="operador",
        required_fields=[
            "run_id",
            "sprint_id",
            "adapter",
            "provider",
            "status",
            "planned_command",
            "context",
            "context_sources",
            "context_hints",
            "required_context",
            "missing_context_hints",
            "missing_required_context",
            "available_context_keys",
            "capability",
            "policy_source",
            "active_policy",
            "selection_reason",
            "suitability_score",
            "alternative_adapters",
            "execute",
        ],
        neighboring_artifacts=["external-dispatch-result.json", "event-log.jsonl"],
    ),
    "external-dispatch-result.json": ArtifactContract(
        name="external-dispatch-result.json",
        objective="registrar o resultado formal de um dispatch externo opt-in",
        generated_by="ExternalExecutorBridge",
        created_at_trigger="após planejamento ou despacho externo",
        mutable_until_gate="a cada novo dispatch",
        approved_by="operador e executor externo quando aplicável",
        required_fields=[
            "adapter",
            "status",
            "planned_command",
            "external_ref",
            "evidence_refs",
            "notes",
            "metadata",
            "context_sources",
            "runtime_profile",
            "runtime_provider",
            "request_metadata",
            "created_at",
        ],
        neighboring_artifacts=["external-dispatch-plan.json", "event-log.jsonl"],
    ),
    "delivery-metrics.json": ArtifactContract(
        name="delivery-metrics.json",
        objective="métricas para gestão e melhoria",
        generated_by="Metrics Aggregator",
        created_at_trigger="após primeiro ciclo de entrega",
        mutable_until_gate="continuamente",
        approved_by="gestão técnica",
        required_fields=["lead_time", "rounds", "pass_rate", "retrabalho", "custo", "falhas_por_tipo"],
        neighboring_artifacts=["event-log.jsonl", "progress.json"],
    ),
    "runtime-hooks.json": ArtifactContract(
        name="runtime-hooks.json",
        objective="registrar hooks de runtime executados e seus resultados",
        generated_by="Runtime Executor",
        created_at_trigger="quando hooks de runtime forem disparados",
        mutable_until_gate="a cada nova execução",
        approved_by="operador",
        required_fields=["run_id", "event", "profile", "provider", "simulated", "context", "raw_context", "resolved_context", "context_hints", "required_context", "missing_context_hints", "missing_required_context", "available_context_keys", "results", "external_evidence_refs", "updated_at"],
        neighboring_artifacts=["event-log.jsonl", "external-evidence-manifest.json"],
    ),
    "external-evidence-manifest.json": ArtifactContract(
        name="external-evidence-manifest.json",
        objective="registrar referências de evidência externa derivadas de runtime/handoff",
        generated_by="Runtime Executor / Operator Service",
        created_at_trigger="quando houver refs externas observáveis",
        mutable_until_gate="a cada nova coleta de evidência",
        approved_by="operador",
        required_fields=["run_id", "event", "simulated", "evidence_refs", "results", "updated_at"],
        neighboring_artifacts=["runtime-hooks.json", "event-log.jsonl"],
    ),
    "ci-result.json": ArtifactContract(
        name="ci-result.json",
        objective="registrar resultado canônico de CI como evidência externa",
        generated_by="Runtime Executor / Operator Service",
        created_at_trigger="quando o runtime processar ci_result",
        mutable_until_gate="a cada nova execução de CI",
        approved_by="operador",
        required_fields=["run_id", "event", "profile", "provider", "simulated", "context", "raw_context", "status", "ci_ref", "evidence_refs", "results", "updated_at"],
        neighboring_artifacts=["runtime-hooks.json", "external-evidence-manifest.json", "event-log.jsonl"],
    ),
    "dashboard.json": ArtifactContract(
        name="dashboard.json",
        objective="visão operacional derivada do estado vivo",
        generated_by="Dashboard",
        created_at_trigger="quando progress/event/metrics estiverem disponíveis",
        mutable_until_gate="continuamente",
        approved_by="gestão técnica e operação",
        required_fields=[
            "project",
            "feature",
            "mode",
            "status",
            "current_gate",
            "current_sprint",
            "gates_summary",
            "event_counts",
            "metrics_summary",
            "blockers",
            "recent_events",
            "generated_at",
        ],
        neighboring_artifacts=["progress.json", "event-log.jsonl", "delivery-metrics.json"],
    ),
}


def get_contract(artifact_name: str) -> Optional[ArtifactContract]:
    return ARTIFACT_CONTRACTS.get(artifact_name)


def validate_artifact(artifact_name: str, data: dict) -> list[str]:
    """Retorna lista de problemas. Lista vazia = válido."""
    contract = get_contract(artifact_name)
    if contract is None:
        return [f"Artefato '{artifact_name}' não tem contrato definido"]

    errors = []
    for field in contract.required_fields:
        if field not in data:
            errors.append(f"Campo obrigatório ausente: {field}")

    return errors


def validate_artifact_on_disk(artifact_path: Path) -> list[str]:
    """
    Valida artefato real no filesystem.
    Verifica: existência, extensão, carga JSON, pareamento md/json.
    Retorna lista de problemas. Lista vazia = válido.
    """
    errors = []
    name = artifact_path.name

    if not artifact_path.exists():
        return [f"Artefato não encontrado: {artifact_path}"]

    # Detectar extensão
    is_json = artifact_path.suffix == ".json"
    is_md = artifact_path.suffix == ".md"

    if is_json:
        try:
            with open(artifact_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return [f"JSON inválido em {name}: {e}"]

        # Validar campos obrigatórios do contrato
        contract = get_contract(name)
        if contract:
            for field in contract.required_fields:
                if field not in data:
                    errors.append(f"Campo obrigatório ausente em {name}: {field}")

    elif is_md:
        content = artifact_path.read_text()
        if not content.strip():
            errors.append(f"Arquivo MD vazio: {name}")

    else:
        # Verificar se não é um arquivo inesperado
        if artifact_path.is_file():
            pass  # outros tipos são aceitos sem validação estrutural

    # Verificar pareamento md/json quando aplicável
    md_path = artifact_path.with_suffix(".md")
    json_path = artifact_path.with_suffix(".json")
    if is_json and md_path.exists():
        # Espera-se que exista versão .md
        pass
    elif is_md and json_path.exists():
        # Verificar que o JSON tem os campos básicos
        try:
            with open(json_path) as f:
                paired = json.load(f)
            if not paired:
                errors.append(f"JSON pareado está vazio: {json_path.name}")
        except json.JSONDecodeError:
            errors.append(f"JSON pareado inválido: {json_path.name}")

    return errors


def validate_workspace_artifacts(artifacts_dir: Path, required_artifacts: list[str]) -> dict[str, list[str]]:
    """
    Valida um conjunto de artefatos obrigatórios em um diretório.
    Retorna dict mapping artifact_name -> lista de erros (vazia = válido).
    """
    results = {}
    for artifact_name in required_artifacts:
        artifact_path = artifacts_dir / artifact_name
        errors = validate_artifact_on_disk(artifact_path)
        results[artifact_name] = errors
    return results


def enrich_spec_contract(
    spec_data: dict,
    authorized_areas: list[str],
    prohibited_areas: list[str],
    handoff_minimum: str,
) -> dict:
    """Enriquece spec.json com áreas autorizadas, proibidas e handoff mínimo."""
    spec_data["areas_autorizadas"] = authorized_areas
    spec_data["areas_proibidas"] = prohibited_areas
    spec_data["handoff_minimum"] = handoff_minimum
    return spec_data
