"""Runtime facade (read/write and shell execution helpers)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass
class RuntimeResult:
    command: str
    returncode: int
    stdout: str = ""
    stderr: str = ""


class RuntimeAdapter:
    def __init__(self, workdir: Path) -> None:
        self.workdir = Path(workdir)

    def read_text(self, path: str | Path) -> str:
        target = self.workdir / path
        return target.read_text(encoding="utf-8")

    def write_text(self, path: str | Path, content: str) -> None:
        target = self.workdir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def list_tree(self, pattern: str | None = None) -> list[str]:
        if pattern:
            return [str(item) for item in self.workdir.glob(pattern)]
        return [str(item) for item in self.workdir.glob("**/*") if item.is_file()]

    def run_command(self, command: list[str], timeout: int = 60) -> RuntimeResult:
        process = subprocess.run(
            command,
            cwd=str(self.workdir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return RuntimeResult(
            command=" ".join(command),
            returncode=process.returncode,
            stdout=process.stdout or "",
            stderr=process.stderr or "",
        )
