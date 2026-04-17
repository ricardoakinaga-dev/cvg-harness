"""
Common types shared across the CVG Harness.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


class Mode(str, Enum):
    """Modo operacional."""
    FAST = "FAST"
    ENTERPRISE = "ENTERPRISE"


class Phase(str, Enum):
    """Fase do fluxo."""
    INTAKE = "intake"
    CLASSIFICATION = "classification"
    RESEARCH = "research"
    PRD = "prd"
    SPEC = "spec"
    LINT = "lint"
    SPRINT = "sprint"
    EXECUTION = "execution"
    EVALUATION = "evaluation"
    RELEASE = "release"


class Status(str, Enum):
    """Status do fluxo ou sprint."""
    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"


class GateState(str, Enum):
    """Estado de um gate. Fonte canônica."""
    NOT_STARTED = "not_started"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    WAIVED = "waived"


@dataclass
class TimestampMixin:
    """Mixins que adiciona timestamp."""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class VersionMixin:
    """Mixin que adiciona versionamento."""
    version: str = "v1"
    previous_version: Optional[str] = None


# Constantes
DEFAULT_WORKSPACE = ".cvg-harness"
ARTIFACTS_DIR = "artifacts"
REPORTS_DIR = "reports"

# Dimensões de classificação
DIMENSIONS = [
    "impacto_arquitetural",
    "modulos_afetados",
    "risco_de_regressao",
    "criticidade_de_negocio",
    "sensibilidade_de_dados",
    "dependencia_externa",
    "reversibilidade",
    "complexidade_de_validacao",
]

# Gates
GATES = [f"GATE_{i}" for i in range(10)]

# Eventos do event log
EVENT_TYPES = [
    "demand_received",
    "demand_classified",
    "research_started",
    "research_approved",
    "prd_approved",
    "spec_created",
    "spec_lint_failed",
    "spec_lint_passed",
    "sprint_started",
    "sprint_planned",
    "sprint_failed",
    "architecture_guard_failed",
    "architecture_guard_passed",
    "evaluation_failed",
    "evaluation_passed",
    "drift_detected",
    "drift_clean",
    "waiver_granted",
    "replan_requested",
    "sprint_approved",
    "release_approved",
    "release_rejected",
    "gate_approved",
    "gate_rejected",
    "gate_waived",
    "gate_in_review",
    "run_started",
    "run_ready_for_execution",
    "operator_paused",
    "operator_resumed",
    "operator_approved",
    "operator_replanned",
    "execution_inputs_registered",
    "evidence_registered",
    "external_execution_requested",
    "external_executor_planned",
    "external_executor_dispatched",
    "external_execution_failed",
    "external_evidence_registered",
    "ci_result_registered",
    "runtime_hooks_executed",
]
