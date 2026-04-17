"""Gerenciamento de plano de execução por demanda."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class PlanStep:
    step_id: str
    name: str
    status: str = "pending"
    notes: str | None = None
    started_at: str | None = None
    ended_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "name": self.name,
            "status": self.status,
            "notes": self.notes,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


class PlanningTool:
    """Plano persistido em `.harness/runs/<run_id>/plan.json`."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = Path(workspace_root).resolve()

    def _run_dir(self, run_id: str) -> Path:
        return self.workspace_root / ".harness" / "runs" / run_id

    def _plan_path(self, run_id: str) -> Path:
        return self._run_dir(run_id) / "plan.json"

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def create_plan(self, run_id: str, steps: list[str]) -> list[PlanStep]:
        payload = [PlanStep(step_id=f"step-{i+1}", name=name) for i, name in enumerate(steps)]
        self._save_plan(run_id, payload)
        return payload

    def update_plan(
        self,
        run_id: str,
        step_id: str,
        status: str,
        notes: str | None = None,
    ) -> list[dict]:
        plan = self._load_plan(run_id)
        found = False
        for step in plan:
            if step["step_id"] == step_id:
                step["status"] = status
                step["notes"] = notes
                if status in {"running"}:
                    step["started_at"] = self._now()
                if status in {"done", "failed", "blocked"}:
                    step["ended_at"] = self._now()
                found = True
                break
        if not found:
            raise KeyError(f"step não encontrado: {step_id}")
        self._plan_path(run_id).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        return plan

    def mark_done(self, run_id: str, step_id: str) -> list[dict]:
        return self.update_plan(run_id, step_id, "done")

    def current_step(self, run_id: str) -> dict[str, Any] | None:
        plan = self._load_plan(run_id)
        for step in plan:
            if step["status"] in {"pending", "running"}:
                return step
        return None

    def _load_plan(self, run_id: str) -> list[dict]:
        path = self._plan_path(run_id)
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return list(raw) if isinstance(raw, list) else []

    def serialize_plan(self, run_id: str) -> dict[str, Any]:
        plan = self._load_plan(run_id)
        return {
            "run_id": run_id,
            "steps": plan,
            "count": len(plan),
            "current_step": self.current_step(run_id),
        }

    def _save_plan(self, run_id: str, steps: list[PlanStep]) -> None:
        payload = [step.to_dict() for step in steps]
        path = self._plan_path(run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
