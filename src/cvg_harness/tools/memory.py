"""Persistência de contexto entre turnos, runs e escopos."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class MemoryItem:
    key: str
    value: Any
    scope: str
    updated_at: str


class ContextMemoryTool:
    def __init__(self, workspace_root: Path, run_id: str | None = None) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.run_id = run_id
        self.project_file = self.workspace_root / ".harness" / "memory.json"
        self.global_file = Path.home() / ".config" / "harness" / "memory.json"
        self.run_file = (
            self.workspace_root / ".harness" / "runs" / run_id / "memory.json"
            if run_id
            else None
        )

    def set_run(self, run_id: str | None) -> None:
        self.run_id = run_id
        self.run_file = (
            self.workspace_root / ".harness" / "runs" / run_id / "memory.json"
            if run_id
            else None
        )

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _load(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return dict(payload) if isinstance(payload, dict) else {}

    def _save(self, path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def save(
        self,
        key: str,
        value: Any,
        scope: str = "project",
    ) -> None:
        scope = str(scope or "project").lower()
        if scope not in {"project", "run", "global"}:
            raise ValueError("scope inválido, use: project | run | global")

        if scope == "global":
            data = self._load(self.global_file)
            data[key] = {"value": value, "updated_at": self._now()}
            self._save(self.global_file, data)
            return
        if scope == "run":
            if not self.run_file:
                raise ValueError("run_id obrigatório para escopo run")
            data = self._load(self.run_file)
            data[key] = {"value": value, "updated_at": self._now()}
            self._save(self.run_file, data)
            return

        data = self._load(self.project_file)
        data[key] = {"value": value, "updated_at": self._now()}
        self._save(self.project_file, data)

    def load(self, key: str) -> Any | None:
        scopes = []
        if self.run_id and self.run_file:
            scopes.append(("run", self.run_file))
        scopes.extend([("project", self.project_file), ("global", self.global_file)])
        for _, path in scopes:
            data = self._load(path)
            if key in data and isinstance(data[key], dict):
                return data[key].get("value")
        return None

    def load_project_context(self) -> dict[str, Any]:
        project_data = self._load(self.project_file)
        simplified = {k: v.get("value") for k, v in project_data.items() if isinstance(v, dict)}
        return simplified

    def append_event(self, event: dict[str, Any], scope: str = "project") -> None:
        item = MemoryItem(
            key="event",
            value=event,
            scope=scope,
            updated_at=self._now(),
        )
        key = item.updated_at + "-" + str(abs(hash(item.key)))
        self.save(key, item.__dict__, scope=scope)
