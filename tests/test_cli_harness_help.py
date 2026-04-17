"""Testes de CLI do comando principal `harness`."""

import subprocess
import json
import sys
import os
import pytest

from pathlib import Path

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


def test_harness_help_exposes_prompt_first_flags() -> None:
    output = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "--help"],
        text=True,
    )
    assert "--provider" in output
    assert "--model" in output
    assert "--api-key" in output
    assert "--non-interactive" in output
    assert "--json" in output
    assert "modo técnico" in output.lower() or "debug" in output.lower()
    assert "harness" in output.lower()
    assert "status" in output.lower()
    assert "resume" in output.lower()
    assert "history" in output.lower()
    assert "config" in output.lower()


def test_harness_help_subcommand_prints_usage() -> None:
    output = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "help"],
        text=True,
    )
    assert "harness" in output.lower()
    assert "status" in output.lower()
    assert "debug" in output.lower()


def test_harness_resume_subcommand_uses_active_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)
    agent._new_demand("criar módulo de permissões por setor")

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "resume"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    assert "Retoma da run" in out
    assert "Demanda:" in out


def test_harness_history_subcommand_returns_session_turns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)
    text = "adicionar autenticação OAuth2 com Google"
    agent.session.append_turn("user", text, "new_demand", "cli")
    _ = agent._new_demand(text)
    _ = agent._status()

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "history"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    assert "Histórico da sessão atual" in out
    assert "adicionar autenticação OAuth2 com Google" in out


def test_harness_history_subcommand_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)
    text = "revisar projeto e planejar a modularização da agenda"
    agent.session.append_turn("user", text, "new_demand", "cli")
    _ = agent._new_demand(text)

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "history", "--json"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    payload = json.loads(out)
    assert payload["status"] == "ok"
    assert payload["count"] >= 1


def test_harness_inspect_subcommand_no_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "inspect"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    assert "Sem demanda ativa para inspeção." in out


def test_harness_inspect_subcommand_with_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)
    demand = "criar módulo de permissões por setor"
    agent._new_demand(demand)

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "inspect"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    assert "Run:" in out
    assert "Demanda:" in out
    assert demand in out


def test_harness_inspect_subcommand_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)
    demand = "adicionar autenticação OAuth2 com Google"
    agent._new_demand(demand)

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "inspect", "--json"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    payload = json.loads(out)
    assert payload["status"] == "ok"
    assert payload["demand"] == demand
    assert payload["run_id"]
    assert isinstance(payload["artifacts"], list)


def test_harness_status_json_without_active_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "status", "--json"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    payload = json.loads(out)
    assert payload["status"] == "no_active_run"
    assert "Sem demanda ativa." in payload["message"]


def test_harness_json_flag_before_subcommand(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)
    _ = agent._new_demand("módulo de permissões por perfil")

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "--json", "status"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    payload = json.loads(out)
    assert payload["status"] == "ok"
    assert payload["run_id"]
    assert payload["demand"] == "módulo de permissões por perfil"


def test_harness_status_subcommand_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)
    text = "adicionar autenticação OAuth2 com Google"
    agent._new_demand(text)

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "status", "--json"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    payload = json.loads(out)
    assert payload["status"] == "ok"
    assert payload["run_id"]
    assert payload["demand"] == text


def test_harness_resume_subcommand_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    _setup_global_config(home)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")

    workspace = tmp_path / "project"
    workspace.mkdir()
    agent = FrontAgent(workspace=workspace, non_interactive=True)
    agent.boot(require_provider=True)
    _ = agent._new_demand("módulo de permissões por perfil")

    out = subprocess.check_output(
        [sys.executable, "-m", "cvg_harness.cli.harness", "resume", "--json"],
        text=True,
        cwd=str(workspace),
        env={
            **os.environ,
            "HOME": str(home),
            "ANTHROPIC_API_KEY": "x",
            "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
        },
    )
    payload = json.loads(out)
    assert payload["status"] == "ok"
    assert payload["action"] == "resume"
