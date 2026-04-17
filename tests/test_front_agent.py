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


def _seed_project(workspace: Path) -> None:
    (workspace / "src" / "auth").mkdir(parents=True)
    (workspace / "src" / "auth" / "login.py").write_text(
        "def login():\n    return True\n"
    )


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


def test_front_agent_completion_summary_aggregates_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    _seed_project(workspace)

    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)

    _ = agent._new_demand("criar módulo de permissões por setor")
    agent.service.approve()
    completed = agent.service.continue_run(
        changed_files=["src/auth/login.py"],
        evidence=[
            "implementação dos arquivos",
            "testes unitários",
            "logs de execução",
            "implementação do módulo auth",
            "testes do módulo auth",
        ],
    )
    assert completed["run"]["operator_status"] == "completed"

    summary = agent._summarize_run(completed, "Demanda concluída.")
    assert "Demanda concluída." in summary
    assert "Resumo da entrega:" in summary
    assert "release readiness:" in summary
    assert "evidências coletadas:" in summary
    assert "arquivos alterados: src/auth/login.py" in summary


def test_doctor_reports_provider_base_url_and_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    workspace = tmp_path / "project"
    workspace.mkdir()
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://example.minimax.test/anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)

    output = agent._doctor()
    assert "provider base_url: https://example.minimax.test/anthropic" in output
    assert "ANTHROPIC_BASE_URL: ok" in output


def test_front_agent_full_loop_completes_and_summarizes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    _seed_project(workspace)

    inputs = _iter_inputs(
        [
            "status",
            "criar módulo de permissões por setor",
            "aprovar",
            "src/auth/login.py implementação dos arquivos testes unitários logs de execução implementação do módulo auth testes do módulo auth",
            "resumo",
            "sair",
        ]
    )
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.start()
    output = capsys.readouterr().out

    assert "Sem demanda ativa. Inicie uma demanda em linguagem natural." in output
    assert "Demanda recebida e roteada" in output
    assert "Sprint aprovada. Envie evidências para continuar." in output
    assert "Demanda não concluída ainda (active)." in output
    assert "Pendência: provide_execution_inputs" in output
    assert "Até mais." in output
