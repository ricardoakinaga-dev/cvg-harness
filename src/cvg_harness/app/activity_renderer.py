"""Renderer de atividade do terminal com spinner animado."""

from __future__ import annotations

import os
import sys
import threading
import time
from typing import Any


class ActivityRenderer:
    """Feedback visual de status curto para operações de longa duração."""

    FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧")
    FRAME_DELAY_SECONDS = 0.1
    START_DELAY_SECONDS = 0.3

    def __init__(self, stream: Any = None) -> None:
        self._stream = stream or sys.stdout
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._shutdown = threading.Event()
        self._pause_until = 0.0

        self.current: str | None = None
        self._label = ""
        self._frame_idx = 0
        self._running = False
        self._started_at = 0.0
        self._should_animate = False

    def _is_ci_or_non_tty(self) -> bool:
        env = os.environ
        if env.get("CI") == "1":
            return True
        if env.get("GITHUB_ACTIONS") == "true":
            return True
        if env.get("PYTEST_CURRENT_TEST"):
            return True
        if env.get("TERM") == "dumb":
            return True
        try:
            return not bool(self._stream.isatty())
        except Exception:
            return True

    @property
    def _animate(self) -> bool:
        return not self._is_ci_or_non_tty()

    def _normalize(self, label: str) -> str:
        value = (label or "").strip()
        return value or "Analisando"

    def _clean_line(self) -> None:
        self._stream.write("\r\033[2K")

    def _write(self, text: str, flush: bool = True) -> None:
        self._stream.write(text)
        if flush:
            self._stream.flush()

    def _render_loop(self) -> None:
        while not self._shutdown.is_set():
            time.sleep(self.FRAME_DELAY_SECONDS)
            with self._lock:
                if not self._running:
                    continue
                if not self._should_animate:
                    continue
                if time.monotonic() - self._started_at < self.START_DELAY_SECONDS:
                    continue
                if time.monotonic() < self._pause_until:
                    continue
                label = self._label
                if not label:
                    continue
                frame = self.FRAMES[self._frame_idx]
                self._frame_idx = (self._frame_idx + 1) % len(self.FRAMES)
                self._clean_line()
                self._write(f"{frame} {label}")

    def _ensure_thread(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._render_loop, daemon=True)
        self._thread.start()

    def start(self, label: str) -> None:
        message = self._normalize(label)
        with self._lock:
            self.current = message
            self._label = message
            self._frame_idx = 0
            self._running = True
            self._started_at = time.monotonic()
            self._should_animate = True

        if not self._animate:
            self._write(f"[{message}...]\n")
            return

        self._ensure_thread()

    def update(self, label: str) -> None:
        message = self._normalize(label)
        with self._lock:
            self.current = message
            self._label = message
            if not self._animate:
                self._write(f"[{message}...]\n")
                return
            if self._running:
                self._frame_idx = 0

    def success(self, message: str) -> None:
        self._finish("✔", message or "Concluído.")

    def error(self, message: str) -> None:
        self._finish("✖", message or "Falhou.")

    def stop(self) -> None:
        self._finish(None, "")

    def _finish(self, icon: str | None, message: str) -> None:
        if self._animate:
            with self._lock:
                if self.current is None and not self._running:
                    return
                self._clean_line()
                if icon:
                    self._write(f"{icon} {message}\n")
                self._running = False
                self.current = None
                self._label = ""
                self._should_animate = False
                self._frame_idx = 0
                return

        with self._lock:
            if self.current is None and not self._running and not message:
                return
            if icon:
                self._write(f"{icon} {message}\n")
            self._running = False
            self.current = None
            self._label = ""
            self._should_animate = False
            self._frame_idx = 0

    def log(self, message: str) -> None:
        if not message:
            return
        if self._animate:
            with self._lock:
                if self._running:
                    self._clean_line()
                    if message:
                        self._pause_until = time.monotonic() + 0.2
                        self._write(f"{message}\n")
        else:
            self._write(f"{message}\n")

    def __del__(self) -> None:
        self._shutdown.set()
