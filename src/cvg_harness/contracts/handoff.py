"""
P1-4: Contratos de handoff entre agentes
Todo handoff deve carregar: artefato fonte, versão, objetivo, restrições, dúvidas, evidências.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class HandoffContract:
    source_artifact: str
    source_version: str
    target_agent: str
    objective: str
    restrictions: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    required_evidences: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


HANDOFF_TEMPLATES = {
    "intake_to_research": HandoffContract(
        source_artifact="intake.md",
        source_version="v1",
        target_agent="Research Agent",
        objective="Mapear arquitetura atual, arquivos relevantes, decisões existentes, riscos e restrições",
        restrictions=[],
        open_questions=[],
        required_evidences=["research-notes.md", "system-map.md"],
    ),
    "research_to_prd": HandoffContract(
        source_artifact="research-notes.md",
        source_version="v1",
        target_agent="PRD Agent",
        objective="Converter necessidade em definição de problema, objetivo, escopo e sucesso",
        restrictions=["Não alterar classificação", "Não assumir que problema já está resolvido"],
        open_questions=[],
        required_evidences=["prd.md"],
    ),
    "prd_to_spec": HandoffContract(
        source_artifact="prd.md",
        source_version="v1",
        target_agent="Spec Builder",
        objective="Traduzir PRD e research em especificação técnica executável",
        restrictions=["Manter alinhamento com objetivo do PRD", "Não ampliar escopo"],
        open_questions=[],
        required_evidences=["spec.md", "spec.json"],
    ),
    "spec_to_sprint": HandoffContract(
        source_artifact="spec.json",
        source_version="v1",
        target_agent="Sprint Planner",
        objective="Quebrar SPEC em unidades pequenas, sequenciadas e executáveis",
        restrictions=["Cada sprint deve ter escopo fechado", "Dependências declaradas"],
        open_questions=[],
        required_evidences=["sprint-plan.json", "execution-order.json"],
    ),
    "sprint_to_coder": HandoffContract(
        source_artifact="sprint-plan.json",
        source_version="v1",
        target_agent="Coder Worker",
        objective="Executar apenas a sprint autorizada",
        restrictions=["Não redefine produto", "Não amplia escopo", "Não altera zona proibida"],
        open_questions=[],
        required_evidences=["arquivos alterados", "racional curto", "evidências da sprint"],
    ),
    "coder_to_evaluator": HandoffContract(
        source_artifact="sprint deliverables",
        source_version="v1",
        target_agent="Evaluator",
        objective="Validar resultado com independência",
        restrictions=["Avaliar contra SPEC e critérios", "Não aceitar critério incompleto"],
        open_questions=[],
        required_evidences=["evaluation-report.json"],
    ),
}


def create_handoff(source_artifact: str, source_version: str, target_agent: str, **kwargs) -> HandoffContract:
    return HandoffContract(
        source_artifact=source_artifact,
        source_version=source_version,
        target_agent=target_agent,
        objective=kwargs.get("objective", ""),
        restrictions=kwargs.get("restrictions", []),
        open_questions=kwargs.get("open_questions", []),
        required_evidences=kwargs.get("required_evidences", []),
    )


def save_handoff(handoff: HandoffContract, path) -> None:
    with open(path, "w") as f:
        json.dump(handoff.to_dict(), f, indent=2)


def load_handoff(path) -> HandoffContract:
    with open(path) as f:
        data = json.load(f)
    return HandoffContract(**data)
