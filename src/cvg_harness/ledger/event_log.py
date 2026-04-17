"""
P1-2: Event Log append-only
Trilha imutável de eventos operacionais.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cvg_harness.types import EVENT_TYPES as CANONICAL_EVENT_TYPES

# Fonte única da canônica do ciclo documental+runtime.
EVENT_TYPES = list(CANONICAL_EVENT_TYPES)


@dataclass
class Event:
    timestamp: str
    event_type: str
    actor: str
    artifact_ref: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def create(cls, event_type: str, actor: str, artifact_ref: str = "", metadata: Optional[dict] = None) -> "Event":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            actor=actor,
            artifact_ref=artifact_ref,
            metadata=metadata or {},
        )


class EventLog:
    """Log append-only de eventos operacionais."""

    def __init__(self, log_path: Path):
        self.log_path = log_path

    def append(self, event: Event) -> None:
        """Adiciona evento ao log (append-only)."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def query(self, event_type: Optional[str] = None, actor: Optional[str] = None) -> list[Event]:
        """Consulta eventos por tipo e/ou ator."""
        events = []
        if not self.log_path.exists():
            return events
        with open(self.log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if event_type and data.get("event_type") != event_type:
                    continue
                if actor and data.get("actor") != actor:
                    continue
                events.append(Event(**data))
        return events

    def last_event(self, event_type: Optional[str] = None) -> Optional[Event]:
        """Retorna último evento, opcionalmente filtrado por tipo."""
        events = self.query(event_type=event_type)
        return events[-1] if events else None

    def count(self, event_type: Optional[str] = None) -> int:
        """Conta eventos, opcionalmente filtrados por tipo."""
        return len(self.query(event_type=event_type))


def save_event(event: Event, log_path: Path) -> None:
    """Salva evento único (append)."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(event.to_dict()) + "\n")


def load_events(log_path: Path, event_type: Optional[str] = None) -> list[Event]:
    """Carrega todos os eventos do log."""
    if not log_path.exists():
        return []
    events = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            if event_type and data.get("event_type") != event_type:
                continue
            events.append(Event(**data))
    return events
