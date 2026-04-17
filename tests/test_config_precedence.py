"""Testes de precedência de configuração do modo `harness`."""

from pathlib import Path

from cvg_harness.config import GlobalHarnessConfig, ProviderConfig, load_config, normalize_provider_defaults, save_global_config, save_project_config


def _create_minimal_global_config(root: Path, provider: str = "minimax", model: str = "MiniMax-M2.7") -> None:
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
        default_provider=provider,
        default_model=model,
        providers=providers,
        workspace_dir=".harness",
    )
    save_global_config(config, path=root / ".config" / "harness" / "config.toml")


def _build_workspace(workspace: Path) -> Path:
    workspace.mkdir(parents=True)
    return workspace


def test_precedence_flags_vs_env_vs_local_vs_global(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    workspace = _build_workspace(tmp_path / "project")
    _create_minimal_global_config(home)
    save_project_config(workspace, provider="openrouter", model="openrouter/moonshot")

    monkeypatch.setenv("HARNESS_PROVIDER", "openai")
    monkeypatch.setenv("HARNESS_MODEL", "gpt-4o")
    loaded = load_config(workspace)
    assert loaded.provider == "openai"
    assert loaded.model == "gpt-4o"

    explicit = load_config(workspace, explicit_provider="minimax", explicit_model="MiniMax-M2.1")
    assert explicit.provider == "minimax"
    assert explicit.model == "MiniMax-M2.1"


def test_model_name_matching_is_case_insensitive(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home-models"
    monkeypatch.setenv("HOME", str(home))
    workspace = _build_workspace(tmp_path / "project2")
    _create_minimal_global_config(home)

    loaded = load_config(workspace, explicit_provider="minimax", explicit_model="minimax-m2.7-highspeed")
    assert loaded.model == "MiniMax-M2.7-highspeed"


def test_base_url_env_overrides_default_provider_url(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home-url"
    monkeypatch.setenv("HOME", str(home))
    workspace = _build_workspace(tmp_path / "project4")
    _create_minimal_global_config(home)

    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://example.minimax.test/anthropic")
    loaded = load_config(workspace, explicit_provider="minimax")
    assert loaded.provider_cfg.base_url == "https://example.minimax.test/anthropic"


def test_explicit_api_key_is_kept_in_memory_only(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home-key"
    monkeypatch.setenv("HOME", str(home))
    workspace = _build_workspace(tmp_path / "project3")
    _create_minimal_global_config(home)

    loaded = load_config(workspace, explicit_api_key="super-secret")
    assert loaded.explicit_key == "super-secret"
