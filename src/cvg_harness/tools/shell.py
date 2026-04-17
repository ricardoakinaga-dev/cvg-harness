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

    def _normalize_cwd(self, cwd: str | Path | None) -> Path:
        requested = Path(cwd or self.workspace_root)
        if not requested.is_absolute():
            requested = (self.workspace_root / requested).resolve()
        else:
            requested = requested.resolve()

        if requested != self.workspace_root and self.workspace_root not in requested.parents:
            raise PermissionError(
                f"Execução bloqueada: diretório fora do workspace ({requested})"
            )
        return requested

    def _command_parts(self, cmd: str | list[str]) -> list[str]:
        if isinstance(cmd, list):
            return [str(item) for item in cmd]
        try:
            return shlex.split(cmd)
        except ValueError as exc:
            raise ValueError(f"Comando inválido: {cmd}") from exc

    def _event(self, event: str, command: str, metadata: dict | None = None) -> None:
        save_event(
            Event.create(event, "ShellTool", command, {
                "workspace": str(self.workspace_root),
                **(metadata or {}),
            }),
            self.event_log_path,
        )

    def _is_allowed(self, command: str) -> bool:
        tokens = self._command_parts(command)
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

        run_cwd = self._normalize_cwd(cwd)
        command = self._command_parts(cmd)
        if not command:
            raise ValueError("Comando vazio não é permitido.")

        if timeout <= 0:
            raise ValueError("timeout deve ser maior que zero.")

        start = time.time()
        process = subprocess.Popen(
            command,
            shell=False,
            cwd=str(run_cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
        )

        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []
        timed_out = False

        try:
            out, err = process.communicate(timeout=timeout)
            if out:
                stdout_chunks.append(out)
                if stream and on_chunk is not None:
                    for line in out.splitlines(True):
                        on_chunk(line)
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
                "cwd": str(run_cwd),
            },
        )
        return result
