"""
P1-1: Progress Ledger
Estado vivo da execução com atualização contínua.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ProgressLedger:
    project: str
    feature: str
    mode: str  # FAST | ENTERPRISE
    status: str  # in_progress | blocked | completed | failed
    current_gate: str
    current_sprint: str
    artifacts: dict[str, str] = field(default_factory=dict)
    gates: dict[str, str] = field(default_factory=dict)
    rounds: dict[str, int] = field(default_factory=lambda: {"coder": 0, "evaluator": 0, "replan": 0})
    blockers: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=lambda: {"acceptancePassRate": 0.0, "estimatedCostUsd": 0.0})
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def new(cls, project: str, feature: str, mode: str) -> "ProgressLedger":
        return cls(
            project=project,
            feature=feature,
            mode=mode,
            status="in_progress",
            current_gate="GATE_0",
            current_sprint="",
            artifacts={},
            gates={g: "not_started" for g in [f"GATE_{i}" for i in range(10)]},
            rounds={"coder": 0, "evaluator": 0, "replan": 0},
            blockers=[],
            metrics={"acceptancePassRate": 0.0, "estimatedCostUsd": 0.0},
        )

    def update_gate(self, gate: str, state: str) -> None:
        self.gates[gate] = state
        self.current_gate = gate
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def increment_round(self, agent: str) -> None:
        if agent in self.rounds:
            self.rounds[agent] += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def add_blocker(self, blocker: str) -> None:
        if blocker not in self.blockers:
            self.blockers.append(blocker)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def clear_blocker(self, blocker: str) -> None:
        if blocker in self.blockers:
            self.blockers.remove(blocker)
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def set_status(self, status: str) -> None:
        self.status = status
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def artifact_version(self, artifact_name: str, version: str) -> None:
        self.artifacts[artifact_name] = version
        self.updated_at = datetime.now(timezone.utc).isoformat()


def save_progress(ledger: ProgressLedger, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(ledger.to_dict(), f, indent=2)


def load_progress(path: Path) -> ProgressLedger:
    with open(path) as f:
        data = json.load(f)
    return ProgressLedger(**data)
