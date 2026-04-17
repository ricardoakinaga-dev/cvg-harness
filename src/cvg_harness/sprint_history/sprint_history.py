"""
P2-3: Histórico comparativo de sprints
Compara performance entre sprints passadas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class SprintRecord:
    sprint_id: str
    project: str
    feature: str
    mode: str
    duration_hours: float
    rounds: int
    passed: bool
    files_changed: int
    blocked_gates: list[str] = field(default_factory=list)
    artifacts_versions: dict[str, str] = field(default_factory=dict)
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SprintComparison:
    project: str
    sprints: list[SprintRecord]
    avg_duration_hours: float = 0.0
    avg_rounds: float = 0.0
    pass_rate: float = 0.0
    avg_files_changed: float = 0.0
    trend: str = "stable"  # improving | degrading | stable
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class SprintHistory:
    """Mantém histórico de sprints e gera comparações."""

    def __init__(self, history_path: Path):
        self.history_path = history_path

    def append(self, record: SprintRecord) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_path, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def load_all(self) -> list[SprintRecord]:
        if not self.history_path.exists():
            return []
        records = []
        with open(self.history_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(SprintRecord(**json.loads(line)))
        return records

    def compare(self, project: str) -> SprintComparison:
        records = self.load_all()
        if not records:
            return SprintComparison(project=project, sprints=[])

        records.sort(key=lambda r: r.completed_at)
        n = len(records)
        avg_duration = sum(r.duration_hours for r in records) / n
        avg_rounds = sum(r.rounds for r in records) / n
        pass_count = sum(1 for r in records if r.passed)
        avg_files = sum(r.files_changed for r in records) / n

        if n >= 2:
            recent = records[-2:]
            if recent[1].duration_hours < recent[0].duration_hours:
                trend = "improving"
            elif recent[1].duration_hours > recent[0].duration_hours:
                trend = "degrading"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return SprintComparison(
            project=project,
            sprints=records,
            avg_duration_hours=avg_duration,
            avg_rounds=avg_rounds,
            pass_rate=pass_count / n,
            avg_files_changed=avg_files,
            trend=trend,
        )


def save_comparison(comparison: SprintComparison, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(comparison.to_dict(), f, indent=2)
