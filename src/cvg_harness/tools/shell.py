"""Execução controlada de comandos no workspace."""

from __future__ import annotations

import subprocess
import time
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

from cvg_harness.ledger.event_log import Event, save_event


StreamCallback = Callable[[str], None]


@dataclass
class ShellResult:
    command: str
    return_code: int
    stdout: str
    stderr: str
    elapsed_ms: float
    timed_out: bool = False
    metadata: dict = field(default_factory=dict)


class ShellTool:
    def __init__(
        self,
        workspace_root: Path,
        event_log_path: Path | None = None,
        allowed_commands: Iterable[str] | None = None,
        denied_commands: Iterable[str] | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.event_log_path = event_log_path or (
            self.workspace_root / ".harness" / "logs" / "tool-events.jsonl"
        )
        whitelist = {
            item.strip().lower() for item in (allowed_commands or []) if item.strip()
        }
        self._allowed: set[str] | None = whitelist or None
        denylist = {item.strip().lower() for item in (denied_commands or []) if item.strip()}
        self._denied: set[str] | None = denylist or None

    def _event(self, event: str, command: str, metadata: dict | None = None) -> None:
        save_event(
            Event.create(event, "ShellTool", command, {
                "workspace": str(self.workspace_root),
                **(metadata or {}),
            }),
            self.event_log_path,
        )

    def _is_allowed(self, command: str) -> bool:
        try:
            tokens = shlex.split(command.strip())
        except ValueError:
            tokens = command.strip().split()
        if not tokens:
            return False
        executable = tokens[0].lower()
        if executable in self._denied if self._denied else False:
            return False
        if self._allowed is None:
            return True
        return executable in self._allowed

    def run(
        self,
        cmd: str | list[str],
        timeout: int = 60,
        cwd: str | Path | None = None,
        stream: bool = False,
        on_chunk: StreamCallback | None = None,
    ) -> ShellResult:
        raw_command = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if not self._is_allowed(raw_command):
            raise PermissionError(f"comando não permitido pela whitelist: {raw_command}")

        start = time.time()
        process = subprocess.Popen(
            cmd if isinstance(cmd, list) else cmd,
            shell=isinstance(cmd, str),
            cwd=str(cwd or self.workspace_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
        )

        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []
        timed_out = False

        try:
            if stream and process.stdout is not None and on_chunk is not None:
                for line in process.stdout:
                    stdout_chunks.append(line)
                    on_chunk(line)
            out, err = process.communicate(timeout=timeout)
            if out:
                stdout_chunks.append(out)
            if err:
                stderr_chunks.append(err)
        except subprocess.TimeoutExpired:
            process.kill()
            out, err = process.communicate()
            if out:
                stdout_chunks.append(out)
            if err:
                stderr_chunks.append(err)
            timed_out = True
        finally:
            return_code = process.returncode or 0

        elapsed = (time.time() - start) * 1000.0
        result = ShellResult(
            command=raw_command,
            return_code=return_code,
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            elapsed_ms=elapsed,
            timed_out=timed_out,
            metadata={
                "timeout": timeout,
                "cwd": str(cwd or self.workspace_root),
            },
        )
        self._event(
            "shell_run",
            raw_command,
            {
                "return_code": return_code,
                "elapsed_ms": elapsed,
                "timed_out": timed_out,
            },
        )
        return result
