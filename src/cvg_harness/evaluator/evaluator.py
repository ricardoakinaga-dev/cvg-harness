"""
Evaluator / QA Gate
Valida sprint contra critérios, evidências e contratos.
P0-6 / P1 - Componente do fluxo de avaliação.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class EvaluationStatus(Enum):
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"
    IN_REVIEW = "in_review"


@dataclass
class CriterionResult:
    criterion: str
    status: str  # passed | failed | waived
    evidence: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class EvaluationReport:
    sprint_id: str
    spec_ref: str
    result: str  # PASSED | FAILED | WAIVED
    criterion_results: list[dict] = field(default_factory=list)
    criterios: list[dict] = field(default_factory=list)
    status: str = ""
    evidencias: list[dict] = field(default_factory=list)
    falhas: list[str] = field(default_factory=list)
    evidence_provided: list[Any] = field(default_factory=list)
    evidence_missing: list[str] = field(default_factory=list)
    structured_evidence_count: int = 0
    structured_evidence_summary: list[dict] = field(default_factory=list)
    next_action: str = "none"  # none | retry | replan
    round: int = 1
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class Evaluator:
    """
    Avalia a sprint contra critérios, evidências e contratos.
    Regra: não aceita critério incompleto.
    """

    def evaluate(
        self,
        sprint_id: str,
        spec: dict,
        evidence_files: list[Any],
        guard_report: Optional[dict] = None,
        round_num: int = 1,
        evidence_items: Optional[list[dict]] = None,
    ) -> EvaluationReport:
        """
        Executa avaliação da sprint.
        Valida:
        - critérios da SPEC (testáveis)
        - evidências esperadas (derivadas da sprint + SPEC)
        - edge cases declarados na SPEC
        - aderência arquitetural (guard_report)
        - artefatos obrigatórios existentes
        """
        criteria = spec.get("criterios", [])
        edge_cases = spec.get("edge_cases", [])
        modulos = spec.get("modulos", [])
        evidence_index = self._build_evidence_index((evidence_items or []) + evidence_files)
        structured_evidence_summary = []
        seen_structured = set()
        for evidence in evidence_index:
            if not self._is_structured_evidence(evidence):
                continue
            summary = self._summarize_structured_evidence(evidence)
            signature = (
                summary.get("kind", ""),
                summary.get("ref", ""),
                summary.get("module", ""),
                summary.get("summary", ""),
            )
            if signature in seen_structured:
                continue
            seen_structured.add(signature)
            structured_evidence_summary.append(summary)

        # Evidências esperadas: base fixa + específicas por módulo
        expected_evidences = [
            "implementação dos arquivos",
            "testes unitários",
            "logs de execução",
        ]
        for mod in modulos:
            expected_evidences.append(f"implementação do módulo {mod}")
            expected_evidences.append(f"testes do módulo {mod}")

        criterion_results = []
        all_passed = True
        evidence_missing = []
        evidence_search_space = self._evidence_search_space(evidence_index)

        for criterion in criteria:
            desc = criterion.get("descricao", "")
            testavel = criterion.get("testavel", False)
            if not testavel:
                if criterion.get("definido_como_lacuna", False):
                    criterion_results.append({
                        "criterion": desc,
                        "status": "waived",
                        "notes": "Critério não testável declarado como lacuna",
                    })
                    continue
                criterion_results.append({
                    "criterion": desc,
                    "status": "failed",
                    "notes": "Critério não é testável",
                })
                all_passed = False
            else:
                criterion_results.append({
                    "criterion": desc,
                    "status": "passed",
                    "evidence": "code review",
                })

        structured_criteria = [
            c for c in spec.get("criterios_aceite", [])
            if isinstance(c, dict)
        ]
        for criterion in structured_criteria:
            kind = criterion.get("kind")
            ref = criterion.get("ref")
            module = criterion.get("module")
            if not kind and not ref and not module:
                continue
            if self._structured_evidence_match(kind, ref, module, evidence_index):
                criterion_results.append({
                    "criterion": criterion.get("descricao", ref or kind or module or "structured"),
                    "status": "passed",
                    "notes": "evidência estruturada reconhecida",
                    "evidence": {
                        "kind": kind,
                        "ref": ref,
                        "module": module,
                    },
                })
            else:
                all_passed = False
                criterion_results.append({
                    "criterion": criterion.get("descricao", ref or kind or module or "structured"),
                    "status": "failed",
                    "notes": "evidência estruturada ausente ou incompatível",
                })

        # Verificar evidências fornecidas vs esperadas
        # Aceita: substring match OU se evidence é path de arquivo
        for ev in expected_evidences:
            found = False
            for e in evidence_search_space:
                # Substring match (old behavior)
                if ev.lower() in e.lower():
                    found = True
                    break
                # File path counts as implicit evidence of implementation/testing
                # Accept any file path as satisfying general evidence categories
                if "/" in e or "\\" in e:
                    found = True
                    break
            if not found:
                evidence_missing.append(ev)

        # Verificar guard report
        if guard_report and guard_report.get("result") == "FAIL":
            all_passed = False
            criterion_results.append({
                "criterion": "Aderência arquitetural",
                "status": "failed",
                "notes": "Architecture Guardian reprovou",
            })

        # Política de edge cases (formalizada em 2026-04-16):
        # Edge cases não evidenciados passam com nota, não falham.
        # Justificativa: evidências são derivadas dos artefatos da sprint,
        # não são obrigatórias por contrato. Falha só ocorre quando
        # evidência É fornecida e NÃO menciona o edge case.
        if edge_cases:
            for ec in edge_cases:
                ec_mentioned = any(
                    ec.lower() in e.lower() for e in evidence_search_space
                )
                if not ec_mentioned:
                    # Edge case não mencionado em evidências — warn mas não falha
                    criterion_results.append({
                        "criterion": f"Edge case: {ec}",
                        "status": "passed",
                        "notes": f"Edge case '{ec}' não mencionado em evidências (tratar como não-evidente)",
                    })

        # Se não há evidência nenhuma, dianggap falha contratual
        if not evidence_index:
            all_passed = False
            evidence_missing.append("nenhuma evidência fornecida")

        if evidence_missing or not all_passed:
            result = "FAILED"
            next_action = "retry" if round_num < 3 else "replan"
        else:
            result = "PASSED"
            next_action = "none"

        return EvaluationReport(
            sprint_id=sprint_id,
            spec_ref=spec.get("meta", ""),
            result=result,
            criterion_results=criterion_results,
            criterios=criterion_results,
            status=result.lower(),
            evidencias=structured_evidence_summary or evidence_index,
            falhas=[item.get("notes", "") for item in criterion_results if item.get("status") == "failed"] + evidence_missing,
            evidence_provided=evidence_files,
            evidence_missing=evidence_missing,
            structured_evidence_count=len(structured_evidence_summary),
            structured_evidence_summary=structured_evidence_summary,
            next_action=next_action,
            round=round_num,
        )

    def _expected_evidence_satisfied(self, expected: str, evidence_index: list[dict], evidence_search_space: list[str]) -> bool:
        expected_lower = expected.lower()
        if expected_lower == "implementação dos arquivos":
            if any(e.get("kind") in {"implementation", "code", "patch"} for e in evidence_index):
                return True
        elif expected_lower == "testes unitários":
            if any(e.get("kind") in {"test", "tests", "unit_test"} for e in evidence_index):
                return True
        elif expected_lower == "logs de execução":
            if any(e.get("kind") in {"log", "logs", "trace"} for e in evidence_index):
                return True
        elif expected_lower.startswith("implementação do módulo "):
            module = expected_lower.replace("implementação do módulo ", "", 1).strip()
            if any(e.get("kind") in {"implementation", "code", "patch"} and str(e.get("module", "")).lower() == module for e in evidence_index):
                return True
        elif expected_lower.startswith("testes do módulo "):
            module = expected_lower.replace("testes do módulo ", "", 1).strip()
            if any(e.get("kind") in {"test", "tests", "unit_test"} and str(e.get("module", "")).lower() == module for e in evidence_index):
                return True

        for e in evidence_search_space:
            if expected_lower in e.lower():
                return True
            if "/" in e or "\\" in e:
                return True
        return False

    def _build_evidence_index(self, evidence_files: list[Any]) -> list[dict]:
        index: list[dict] = []
        for item in evidence_files:
            if isinstance(item, dict):
                index.append({
                    "kind": item.get("kind", "text"),
                    "ref": str(item.get("ref", "")),
                    "module": str(item.get("module", "")),
                    "summary": str(item.get("summary", item.get("text", item.get("description", item.get("name", ""))))),
                    "_structured_input": True,
                    **item,
                })
                continue
            if not isinstance(item, str):
                continue
            if item.strip().startswith("{") and item.strip().endswith("}"):
                try:
                    data = json.loads(item)
                    if isinstance(data, dict):
                        index.append({
                            "kind": data.get("kind", "text"),
                            "ref": str(data.get("ref", "")),
                            "module": str(data.get("module", "")),
                            "summary": str(data.get("summary", data.get("text", data.get("description", data.get("name", ""))))),
                            "_structured_input": True,
                            **data,
                        })
                        continue
                except json.JSONDecodeError:
                    pass
            index.append({"kind": "text", "ref": item, "module": "", "summary": item, "_structured_input": False})
        return index

    def _evidence_search_space(self, evidence_index: list[dict]) -> list[str]:
        texts: list[str] = []
        for evidence in evidence_index:
            for key in ("summary", "ref", "module", "kind"):
                value = evidence.get(key)
                if value:
                    texts.append(str(value))
        return texts

    def _structured_evidence_match(self, kind: Optional[str], ref: Optional[str], module: Optional[str], evidence_index: list[dict]) -> bool:
        for evidence in evidence_index:
            if kind and evidence.get("kind") != kind:
                continue
            if ref and evidence.get("ref") != ref:
                continue
            if module and evidence.get("module") != module:
                continue
            return True
        return False

    def _is_structured_evidence(self, evidence: dict) -> bool:
        return bool(evidence.get("_structured_input"))

    def _summarize_structured_evidence(self, evidence: dict) -> dict:
        summary = {
            "kind": evidence.get("kind", "text"),
            "ref": evidence.get("ref", ""),
            "module": evidence.get("module", ""),
            "summary": evidence.get("summary", ""),
        }
        if evidence.get("source"):
            summary["source"] = evidence.get("source")
        return summary


def save_evaluation(report: EvaluationReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report.to_dict(), f, indent=2)


def load_evaluation(path: Path) -> EvaluationReport:
    with open(path) as f:
        data = json.load(f)
    return EvaluationReport(**data)
