"""Sessão persistida do agente `harness`."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ChatTurn:
    role: str
    text: str
    intent: str
    actor: str
    timestamp: str


@dataclass
class SessionState:
    workspace: str
    run_id: str | None = None
    provider: str = "minimax"
    model: str | None = None
    last_prompt: str | None = None
    history: list[dict] | None = None

    def as_dict(self) -> dict:
        return asdict(self) | {"history": self.history or []}


class SessionManager:
    def __init__(self, workspace: Path, state_dir: str = ".harness") -> None:
        self.workspace = Path(workspace)
        self.state_dir = self.workspace / state_dir
        self.session_path = self.state_dir / "session" / "current.json"
        self.history_path = self.state_dir / "session" / "history.jsonl"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def current(self) -> SessionState:
        if not self.session_path.exists():
            return SessionState(workspace=str(self.workspace))
        payload = json.loads(self.session_path.read_text(encoding="utf-8"))
        payload["history"] = payload.get("history", [])
        return SessionState(**payload)

    def save(self, state: SessionState) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        data = state.as_dict()
        self.session_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def append_turn(self, role: str, text: str, intent: str, actor: str) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        state = self.current()
        state.history = state.history or []
        turn = ChatTurn(
            role=role,
            text=text,
            intent=intent,
            actor=actor,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        state.history.append(asdict(turn))
        self.save(state)
        with open(self.history_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(turn), ensure_ascii=False) + "\n")

    def set_active_run(self, run_id: str | None) -> None:
        state = self.current()
        state.run_id = run_id
        self.save(state)

    def set_context(self, provider: str, model: str) -> None:
        state = self.current()
        state.provider = provider
        state.model = model
        self.save(state)
