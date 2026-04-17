"""Gerencia estrutura local de estado por projeto."""

from __future__ import annotations

from pathlib import Path


class WorkspaceManager:
    def __init__(self, root: Path | None = None, state_dir: str = ".harness") -> None:
        self.root = Path(root or Path.cwd())
        self.state_dir = self.root / state_dir
        self.runs_dir = self.state_dir / "runs"
        self.artifacts_dir = self.state_dir / "artifacts"
        self.reports_dir = self.state_dir / "reports"
        self.logs_dir = self.state_dir / "logs"
        self.ledgers_dir = self.state_dir / "ledgers"
        self.session_dir = self.state_dir / "session"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        for path in [
            self.state_dir,
            self.runs_dir,
            self.artifacts_dir,
            self.reports_dir,
            self.logs_dir,
            self.ledgers_dir,
            self.session_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self.root

    def describe(self) -> dict[str, str]:
        return {
            "workspace": str(self.root),
            "state_dir": str(self.state_dir),
            "runs": str(self.runs_dir),
            "artifacts": str(self.artifacts_dir),
            "reports": str(self.reports_dir),
            "logs": str(self.logs_dir),
            "ledgers": str(self.ledgers_dir),
            "session": str(self.session_dir),
        }
