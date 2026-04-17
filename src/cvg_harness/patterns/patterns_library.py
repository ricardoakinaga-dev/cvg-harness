"""
P2-4: Biblioteca de padrões reutilizáveis
Padrões para spec, lint rules, guard rules, fallback, etc.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Pattern:
    name: str
    category: str  # spec | lint | guard | fallback | handoff | template
    description: str
    content: dict
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


PATTERNS_LIBRARY = {
    "spec_api_crud": Pattern(
        name="spec_api_crud",
        category="spec",
        description="Template para SPEC de CRUD de API REST",
        content={
            "meta": "Implementar CRUD completo para {recurso}",
            "modulos": ["{modulo}"],
            "areas_autorizadas": ["{modulo}/api", "{modulo}/models"],
            "areas_proibidas": ["{modulo}/legacy", "shared/legacy"],
            "contratos": [
                {
                    "nome": "create_{recurso}",
                    "tipo": "api",
                    "method": "POST",
                    "path": "/api/{recurso}",
                    "payload": {"nome": "string", "descricao": "string"},
                },
                {
                    "nome": "get_{recurso}",
                    "tipo": "api",
                    "method": "GET",
                    "path": "/api/{recurso}/{id}",
                },
            ],
            "edge_cases": [
                "ID inexistente retorna 404",
                "Payload inválido retorna 422",
                "Duplicata retorna 409",
            ],
            "rollback": "Reverter migração e remover arquivos criados",
        },
        tags=["api", "crud", "rest"],
    ),
    "lint_no_vague_modules": Pattern(
        name="lint_no_vague_modules",
        category="lint",
        description="Regra bloqueante: módulos devem ter nome descritivo (min 3 chars)",
        content={
            "rule": "module_name_min_length",
            "severity": "blocking",
            "min_length": 3,
            "message": "Nome de módulo deve ter pelo menos 3 caracteres",
        },
        tags=["modules", "blocking"],
    ),
    "guard_no_prohibited_area": Pattern(
        name="guard_no_prohibited_area",
        category="guard",
        description="Bloqueia alteração em áreas proibidas",
        content={
            "rule": "prohibited_area_touched",
            "severity": "fail",
            "message": "Arquivo em área proibida não pode ser alterado",
        },
        tags=["boundary", "prohibited"],
    ),
    "fallback_retry_local": Pattern(
        name="fallback_retry_local",
        category="fallback",
        description="Retry local após primeira falha do evaluator",
        content={
            "trigger": "evaluator_failure_round_1",
            "action": "retry_local",
            "details": "Retornar ao coder com feedback fechado",
            "do_not": "Alterar PRD ou classificação",
        },
        tags=["evaluator", "retry"],
    ),
    "handoff_coder_worker": Pattern(
        name="handoff_coder_worker",
        category="handoff",
        description="Handoff padrão para Coder Worker",
        content={
            "source_artifact": "sprint-plan.json",
            "target_agent": "Coder Worker",
            "restrictions": [
                "Não redefine produto",
                "Não amplia escopo",
                "Não altera zona proibida",
            ],
            "required_evidences": [
                "arquivos alterados",
                "racional curto",
                "testes executados",
            ],
        },
        tags=["coder", "handoff"],
    ),
    "template_prd_basic": Pattern(
        name="template_prd_basic",
        category="template",
        description="Template básico de PRD",
        content={
            "sections": ["problema", "objetivo", "kpis", "escopo", "fora_de_escopo", "user_stories", "riscos"],
            "required_each": True,
        },
        tags=["prd", "template"],
    ),
    "template_spec_json": Pattern(
        name="template_spec_json",
        category="template",
        description="Estrutura mínima de spec.json",
        content={
            "required_fields": ["meta", "modulos", "areas_autorizadas", "areas_proibidas", "contratos", "sprints", "criterios", "edge_cases", "observabilidade", "rollback"],
            "version_field": True,
            "change_reason_required": True,
        },
        tags=["spec", "template"],
    ),
}


def get_pattern(category: Optional[str] = None) -> dict[str, Pattern]:
    if category:
        return {k: v for k, v in PATTERNS_LIBRARY.items() if v.category == category}
    return PATTERNS_LIBRARY


def save_patterns(library_path, patterns: dict[str, Pattern]) -> None:
    data = {k: v.to_dict() for k, v in patterns.items()}
    with open(library_path, "w") as f:
        json.dump(data, f, indent=2)


def load_patterns(library_path) -> dict[str, Pattern]:
    with open(library_path) as f:
        data = json.load(f)
    return {k: Pattern(**v) for k, v in data.items()}
