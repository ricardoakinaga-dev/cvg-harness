"""Testes de integração mínima para o loop conversacional do front-agent."""

from __future__ import annotations

import builtins
from pathlib import Path
from typing import Iterator

import pytest

from cvg_harness.app.agent import FrontAgent
from cvg_harness.config import GlobalHarnessConfig, ProviderConfig, save_global_config, normalize_provider_defaults


def _setup_global_config(home: Path) -> None:
    defaults = normalize_provider_defaults()
    providers: dict[str, ProviderConfig] = {}
    for name, payload in defaults.items():
        providers[name] = ProviderConfig(
            name=name,
            base_url=payload["base_url"],
            api_key_env=payload["api_key_env"],
            models=list(payload["models"]),
            default_model=payload["default_model"],
        )
    config = GlobalHarnessConfig(
        default_provider="minimax",
        default_model=defaults["minimax"]["default_model"],
        providers=providers,
        workspace_dir=".harness",
    )
    save_global_config(config, path=home / ".config" / "harness" / "config.toml")


def _iter_inputs(values: list[str]) -> Iterator[str]:
    for item in values:
        yield item
    while True:
        raise RuntimeError("entrada não esperada no teste")


def test_front_agent_start_runs_status_and_exits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()

    inputs = _iter_inputs(["status", "sair"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.start()
    output = capsys.readouterr().out

    assert "Harness iniciado." in output
    assert "Workspace detectado" in output
    assert "Sem demanda ativa. Inicie uma demanda em linguagem natural." in output
    assert "Até mais." in output


def test_select_model_prefers_fast_or_enterprise_variant(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()

    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)

    assert "highspeed" in agent._select_model("FAST").lower()
    assert "highspeed" not in agent._select_model("ENTERPRISE").lower()
