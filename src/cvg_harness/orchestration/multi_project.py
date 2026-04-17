"""
P3-1: Orquestração multi-projeto
Orquestração ampla para múltiplos projetos simultaneamente.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class ProjectFlow:
    project_id: str
    project_name: str
    feature: str
    mode: str
    status: str  # queued | running | blocked | completed | failed
    progress_path: Path
    event_log_path: Path
    current_sprint: str = ""
    priority: int = 0
    blockers: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["progress_path"] = str(self.progress_path)
        d["event_log_path"] = str(self.event_log_path)
        return d


@dataclass
class MultiProjectOrchestrator:
    project_id: str
    flows: dict[str, ProjectFlow] = field(default_factory=dict)
    max_concurrent: int = 3
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)

    def add_flow(self, flow: ProjectFlow) -> None:
        self.flows[flow.project_id] = flow
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def remove_flow(self, project_id: str) -> Optional[ProjectFlow]:
        return self.flows.pop(project_id, None)

    def get_active_flows(self) -> list[ProjectFlow]:
        return [f for f in self.flows.values() if f.status == "running"]

    def get_blocked_flows(self) -> list[ProjectFlow]:
        return [f for f in self.flows.values() if f.status == "blocked"]

    def can_start_new(self) -> bool:
        return len(self.get_active_flows()) < self.max_concurrent

    def queue_priority_sorted(self) -> list[ProjectFlow]:
        queued = [f for f in self.flows.values() if f.status == "queued"]
        queued.sort(key=lambda f: (-f.priority, f.created_at))
        return queued


def save_orchestrator(orchestrator: MultiProjectOrchestrator, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(orchestrator.to_dict(), f, indent=2)


def load_orchestrator(path: Path) -> MultiProjectOrchestrator:
    with open(path) as f:
        data = json.load(f)
    flows = {}
    for pid, fdata in data["flows"].items():
        fdata["progress_path"] = Path(fdata["progress_path"])
        fdata["event_log_path"] = Path(fdata["event_log_path"])
        flows[pid] = ProjectFlow(**fdata)
    data["flows"] = flows
    return MultiProjectOrchestrator(**data)
