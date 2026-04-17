"""Ferramenta de operação segura de arquivos no workspace."""

from __future__ import annotations

import difflib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cvg_harness.ledger.event_log import Event, save_event


@dataclass
class FileOperationResult:
    path: str
    operation: str
    diff: str
    bytes_written: int


class FileSystemTool:
    """Operações de arquivo com escopo forçado no workspace."""

    def __init__(
        self,
        workspace_root: Path,
        event_log_path: Path | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root).resolve()
        self.event_log_path = event_log_path or (
            self.workspace_root / ".harness" / "logs" / "tool-events.jsonl"
        )

    def _to_path(self, path: str | Path) -> Path:
        return Path(path)

    def _resolve(self, path: str | Path) -> Path:
        candidate = self._to_path(path)
        if not candidate.is_absolute():
            candidate = (self.workspace_root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        if candidate != self.workspace_root and self.workspace_root not in candidate.parents:
            raise ValueError(f"Acesso fora do workspace bloqueado: {path}")
        return candidate

    def _event(self, event: str, target: str, metadata: dict[str, Any] | None = None) -> None:
        save_event(
            Event.create(
                event,
                "FileSystemTool",
                target,
                {
                    "workspace": str(self.workspace_root),
                    **(metadata or {}),
                },
            ),
            self.event_log_path,
        )

    def read_file(self, path: str | Path) -> str:
        target = self._resolve(path)
        content = target.read_text(encoding="utf-8")
        self._event("filesystem_read", str(target), {"size": len(content)})
        return content

    def write_file(self, path: str | Path, content: str) -> FileOperationResult:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        previous = ""
        if target.exists():
            previous = target.read_text(encoding="utf-8")
        target.write_text(content, encoding="utf-8")
        diff = "\n".join(
            difflib.unified_diff(
                previous.splitlines(),
                content.splitlines(),
                fromfile=f"a/{target}",
                tofile=f"b/{target}",
                lineterm="",
            )
        )
        self._event("filesystem_write", str(target), {"bytes": len(content.encode("utf-8"))})
        return FileOperationResult(
            path=str(target),
            operation="write",
            diff=diff,
            bytes_written=len(content.encode("utf-8")),
        )

    def _looks_like_unified_patch(self, patch_text: str) -> bool:
        text = patch_text.strip()
        lines = text.splitlines()
        if not lines:
            return False
        return (
            text.startswith("diff")
            or any(line.startswith("@@") for line in lines)
            or any(line.startswith("+++") for line in lines)
            or any(line.startswith("---") for line in lines)
        )

    def _apply_unified_patch(self, patch_text: str, target: Path) -> str:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_text("", encoding="utf-8")
        completed = subprocess.run(
            ["patch", str(target)],
            cwd=str(self.workspace_root),
            input=patch_text.encode("utf-8"),
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "falha ao aplicar patch: "
                + completed.stderr.decode("utf-8", errors="ignore")
            )
        return target.read_text(encoding="utf-8")

    def _apply_full_replacement(self, target: Path, payload: str) -> str:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload, encoding="utf-8")
        return payload

    def edit_file(self, path: str | Path, patch_or_full: str) -> FileOperationResult:
        target = self._resolve(path)
        before = target.read_text(encoding="utf-8") if target.exists() else ""
        patch_mode = self._looks_like_unified_patch(patch_or_full)

        if patch_mode:
            try:
                after = self._apply_unified_patch(patch_or_full, target)
            except Exception:
                after = self._apply_full_replacement(target, patch_or_full)
        else:
            after = self._apply_full_replacement(target, patch_or_full)

        diff = "\n".join(
            difflib.unified_diff(
                before.splitlines(),
                after.splitlines(),
                fromfile=f"a/{target}",
                tofile=f"b/{target}",
                lineterm="",
            )
        )
        self._event("filesystem_edit", str(target), {"patch_mode": patch_mode})
        return FileOperationResult(
            path=str(target),
            operation="edit",
            diff=diff,
            bytes_written=len(after.encode("utf-8")),
        )

    def list_dir(self, path: str | Path = ".") -> list[str]:
        target = self._resolve(path)
        if not target.exists():
            return []
        if not target.is_dir():
            raise ValueError(f"Não é diretório: {target}")
        return sorted(item.name for item in target.iterdir())

    def glob(self, pattern: str, base_path: str | Path | None = None) -> list[str]:
        base = self._resolve(base_path or ".")
        if not base.exists() or not base.is_dir():
            return []
        return sorted(str(path.relative_to(self.workspace_root)) for path in base.glob(pattern))

    def copy(self, src: str | Path, dst: str | Path) -> None:
        source = self._resolve(src)
        dest = self._resolve(dst)
        if source.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(source, dest)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)
        self._event("filesystem_copy", str(dest), {"source": str(source)})
