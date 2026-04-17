"""
Testes para Handoff e Contracts.
"""

import pytest
import tempfile
from pathlib import Path

from cvg_harness.contracts.artifact_contracts import (
    ARTIFACT_CONTRACTS, get_contract, validate_artifact, enrich_spec_contract
)
from cvg_harness.contracts.handoff import create_handoff, HandoffContract


def test_artifact_contracts_all_defined():
    required = [
        "intake.md", "classification.json", "research-notes.md", "system-map.md",
        "prd.md", "spec.md", "spec.json", "spec-lint-report.json",
        "sprint-plan.json", "execution-order.json", "architecture-guard-report.json",
        "evaluation-report.json", "drift-report.json", "progress.json",
        "event-log.jsonl", "delivery-metrics.json",
    ]
    for name in required:
        assert name in ARTIFACT_CONTRACTS, f"Missing contract for {name}"

    # `release-readiness.md` é sidecar humano; o contrato permanece apenas para trilha documental.
    release_md_contract = get_contract("release-readiness.md")
    assert release_md_contract is not None
    assert "sidecar opcional" in release_md_contract.objective

    # `release-readiness-report.json` é o canônico de decisão de release.
    release_json_contract = get_contract("release-readiness-report.json")
    assert release_json_contract is not None
    assert "canônico" in release_json_contract.objective


def test_get_contract():
    contract = get_contract("classification.json")
    assert contract is not None
    assert contract.name == "classification.json"
    assert "dimensions" in contract.required_fields


def test_validate_artifact_valid():
    data = {
        "project": "proj",
        "demand": "feature",
        "mode": "FAST",
        "total_score": 5,
        "dimensions": {},
        "rationale": "test rationale",
        "override_applied": False,
        "classified_by": "planner",
        "timestamp": "2026-04-16T00:00:00Z",
    }
    errors = validate_artifact("classification.json", data)
    assert errors == []


def test_validate_artifact_missing_field():
    data = {"dimensions": {}}
    errors = validate_artifact("classification.json", data)
    assert len(errors) > 0


def test_enrich_spec_contract():
    spec = {"meta": "test"}
    enriched = enrich_spec_contract(
        spec,
        authorized_areas=["src/a"],
        prohibited_areas=["src/legacy"],
        handoff_minimum="SPEC aprovada",
    )
    assert enriched["areas_autorizadas"] == ["src/a"]
    assert enriched["areas_proibidas"] == ["src/legacy"]
    assert enriched["handoff_minimum"] == "SPEC aprovada"


def test_create_handoff():
    h = create_handoff(
        source_artifact="prd.md",
        source_version="v2",
        target_agent="Spec Builder",
        objective="gerar spec",
        restrictions=["não ampliar escopo"],
        open_questions=["dependência externa?"],
        required_evidences=["spec.json"],
    )
    assert h.source_artifact == "prd.md"
    assert h.target_agent == "Spec Builder"
    assert h.restrictions == ["não ampliar escopo"]
