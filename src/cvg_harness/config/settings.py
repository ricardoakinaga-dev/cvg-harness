"""Configuration layer for the terminal-first Harness agent."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import os
from copy import deepcopy

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - py3.10 fallback safety
    tomllib = None


GLOBAL_CONFIG = Path.home() / ".config" / "harness" / "config.toml"
PROJECT_CONFIG = Path(".harness") / "project.toml"


class ConfigValueError(ValueError):
    """Erro de validação de configuração."""


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str
    base_url_env: str = ""
    api_key_env: str = ""
    models: list[str] = field(default_factory=list)
    default_model: str = ""
    enabled: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "base_url": self.base_url,
            "base_url_env": self.base_url_env,
            "api_key_env": self.api_key_env,
            "models": list(self.models),
            "default_model": self.default_model,
            "enabled": self.enabled,
        }


@dataclass
class GlobalHarnessConfig:
    default_provider: str
    default_model: str
    providers: dict[str, ProviderConfig]
    workspace_dir: str = ".harness"

    def as_dict(self) -> dict[str, Any]:
        return {
            "default_provider": self.default_provider,
            "default_model": self.default_model,
            "workspace_dir": self.workspace_dir,
            "providers": {name: provider.as_dict() for name, provider in self.providers.items()},
        }


@dataclass
class LoadedConfig:
    config: GlobalHarnessConfig
    explicit_provider: str | None = None
    explicit_model: str | None = None
    explicit_key: str | None = None
    warnings: list[str] = field(default_factory=list)

    @property
    def provider(self) -> str:
        return (self.explicit_provider or self.config.default_provider).lower()

    @property
    def model(self) -> str:
        return self.explicit_model or self.config.default_model

    @property
    def provider_cfg(self) -> ProviderConfig:
        provider = self.provider
        if provider not in self.config.providers:
            raise ConfigValueError(f"provider desconhecido: {provider}")
        return self.config.providers[provider]

    def with_resolved_api_key(self, override_key: str | None = None) -> "LoadedConfig":
        if override_key:
            return replace(self, explicit_key=override_key)
        if self.explicit_key:
            return self
        env_key = os.getenv(self.provider_cfg.api_key_env)
        return replace(self, explicit_key=env_key)


def normalize_provider_defaults() -> dict[str, dict[str, Any]]:
    """Default provider registry used by the onboarding flow."""
    return {
        "minimax": {
            "name": "minimax",
            "base_url": "https://api.minimax.io/anthropic",
            "base_url_env": "ANTHROPIC_BASE_URL",
            "api_key_env": "ANTHROPIC_API_KEY",
            "models": [
                "MiniMax-M2.7",
                "MiniMax-M2.7-highspeed",
                "MiniMax-M2.5",
                "MiniMax-M2.5-highspeed",
                "MiniMax-M2.1",
                "MiniMax-M2.1-highspeed",
                "MiniMax-M2",
            ],
            "default_model": "MiniMax-M2.7",
        },
        "openai": {
            "name": "openai",
            "base_url": "https://api.openai.com/v1",
            "base_url_env": "OPENAI_BASE_URL",
            "api_key_env": "OPENAI_API_KEY",
            "models": [
                "gpt-4.1",
                "gpt-4o",
                "gpt-4o-mini",
            ],
            "default_model": "gpt-4o-mini",
        },
        "openrouter": {
            "name": "openrouter",
            "base_url": "https://openrouter.ai/api/v1",
            "base_url_env": "OPENROUTER_BASE_URL",
            "api_key_env": "OPENROUTER_API_KEY",
            "models": [
                "openai/gpt-4o-mini",
                "openai/gpt-4.1",
                "google/gemini-2.5-pro",
            ],
            "default_model": "openai/gpt-4o-mini",
        },
    }


def _normalize_name(name: str | None) -> str:
    return (name or "").strip().lower()


def validate_model_name(provider: str, candidate: str | None) -> str:
    provider = _normalize_name(provider)
    provider_defaults = normalize_provider_defaults().get(provider, {})
    models: list[str] = list(provider_defaults.get("models", []))
    if candidate:
        normalized_candidate = candidate.strip()
        for model in models:
            if model == normalized_candidate:
                return model
            if model.lower() == normalized_candidate.lower():
                return model
    if not models:
        raise ConfigValueError(f"provider sem modelos válidos: {provider}")
    # Mantém comportamento previsível sem bloquear customizações.
    return models[0]


def _normalize_model(value: str, available: list[str]) -> str | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    for model in available:
        if model == normalized:
            return model
        if model.lower() == normalized.lower():
            return model
    return None


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = path.read_text(encoding="utf-8")
    if tomllib is None:
        try:
            import toml  # type: ignore
        except Exception as exc:  # pragma: no cover - optional fallback
            raise ConfigValueError(f"Não foi possível ler TOML em {path}: {exc}") from exc
        return toml.loads(data)
    return tomllib.loads(data)


def _write_toml(path: Path, payload: Mapping[str, Any]) -> None:
    # Pequeno serializer toml-like para evitar dependência extra.
    lines: list[str] = []
    for key, value in payload.items():
        if key == "providers":
            continue
        lines.append(f"{key} = {_serialize_toml(value)}")
    providers = payload.get("providers")
    if providers:
        for provider_name, provider_cfg in providers.items():
            if not isinstance(provider_cfg, Mapping):
                continue
            lines.append("")
            lines.append(f"[providers.{provider_name}]")
            for field_name, field_value in provider_cfg.items():
                if field_name == "name":
                    continue
                lines.append(f"{field_name} = {_serialize_toml(field_value)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _serialize_toml(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_serialize_toml(item) for item in value) + "]"
    if isinstance(value, Mapping):
        inner = []
        for k, v in value.items():
            inner.append(f"{k} = {_serialize_toml(v)}")
        return "{ " + ", ".join(inner) + " }"
    return json.dumps(str(value))


def _build_default_config() -> dict[str, Any]:
    defaults = normalize_provider_defaults()
    return {
        "default_provider": "minimax",
        "default_model": defaults["minimax"]["default_model"],
        "workspace_dir": ".harness",
        "providers": {
            name: {
                "base_url": payload["base_url"],
                "base_url_env": payload.get("base_url_env", ""),
                "api_key_env": payload["api_key_env"],
                "models": list(payload["models"]),
                "default_model": payload["default_model"],
            }
            for name, payload in defaults.items()
        },
    }


def _load_provider_payload(payload: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not payload:
        return {}
    providers: dict[str, dict[str, Any]] = {}
    raw = payload.get("providers", {})
    if not isinstance(raw, Mapping):
        return providers
    for name, cfg in raw.items():
        if not isinstance(name, str):
            continue
        if not isinstance(cfg, Mapping):
            continue
        providers[_normalize_name(name)] = dict(cfg)
    return providers


def _merge_payloads(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if key == "providers" and isinstance(value, Mapping):
            providers = result.setdefault("providers", {})
            if isinstance(providers, dict):
                providers.update(_load_provider_payload({"providers": value}))
            continue
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            merged = dict(result.get(key, {}))
            merged.update(value)
            result[key] = merged
        else:
            if value not in (None, ""):
                result[key] = value
    return result


def _load_file_config(path: Path) -> dict[str, Any]:
    payload = _read_toml(path)
    if not isinstance(payload, Mapping):
        return {}
    return {
        "default_provider": payload.get("default_provider", ""),
        "default_model": payload.get("default_model", ""),
        "workspace_dir": payload.get("workspace_dir", ""),
        "providers": _load_provider_payload(payload),
    }


def _normalize_provider_config(name: str, data: Mapping[str, Any]) -> ProviderConfig:
    defaults = normalize_provider_defaults()
    base = defaults[name]
    configured = dict(data)
    model_list = configured.get("models")
    if not isinstance(model_list, Iterable):
        model_list = base["models"]
    models = list(model_list)
    if not models:
        models = list(base["models"])
    base_url = str(configured.get("base_url", base["base_url"]))
    base_url_env = str(configured.get("base_url_env", base.get("base_url_env", "")))
    resolved_base_url = os.getenv(base_url_env, base_url) if base_url_env else base_url
    return ProviderConfig(
        name=name,
        base_url=resolved_base_url,
        base_url_env=base_url_env,
        api_key_env=str(configured.get("api_key_env", base["api_key_env"])),
        models=models,
        default_model=str(configured.get("default_model", models[0])),
        enabled=bool(configured.get("enabled", True)),
    )


def _provider_names_for_selection() -> set[str]:
    return set(normalize_provider_defaults())


def apply_env_overrides(config: GlobalHarnessConfig, provider: str) -> GlobalHarnessConfig:
    provider = _normalize_name(provider)
    if provider not in config.providers:
        return config
    env_key = os.getenv(config.providers[provider].api_key_env)
    # Mantemos o objeto em memória sem persistir chave literal.
    # Não altera outros campos hoje, mas mantém contrato aberto.
    return config if env_key else config


def load_config(
    workspace: Path | None = None,
    explicit_provider: str | None = None,
    explicit_model: str | None = None,
    explicit_api_key: str | None = None,
) -> LoadedConfig:
    """
    Resolve as fontes de configuração na ordem:

    1. flags explícitas
    2. variáveis de ambiente
    3. config local do projeto
    4. config global
    """
    workspace_root = Path(workspace or Path.cwd())

    merged = _build_default_config()
    merged = _merge_payloads(merged, _load_file_config(GLOBAL_CONFIG))
    merged = _merge_payloads(merged, _load_file_config(workspace_root / PROJECT_CONFIG))

    available = _provider_names_for_selection()
    requested_provider = _normalize_name(explicit_provider)
    candidate_provider = requested_provider or _normalize_name(os.getenv("HARNESS_PROVIDER")) or _normalize_name(
        merged.get("default_provider", "minimax")
    )
    warnings: list[str] = []
    if candidate_provider and candidate_provider not in available:
        if requested_provider:
            warnings.append(f"provider explícito inválido '{requested_provider}', usando minimax")
        candidate_provider = "minimax"

    provider_payload = _load_provider_payload({"providers": merged.get("providers", {})}).get(candidate_provider, {})
    all_providers = {}
    for provider_name in _provider_names_for_selection():
        all_payload = _load_provider_payload({"providers": merged.get("providers", {})}).get(provider_name, {})
        all_providers[provider_name] = _normalize_provider_config(provider_name, all_payload)

    default_model = str(merged.get("default_model", "") or all_providers[candidate_provider].default_model)
    explicit_or_env_model = (
        (explicit_model or "").strip()
        or (os.getenv("HARNESS_MODEL") or "").strip()
        or str(default_model or "")
    )

    resolved_model = validate_model_name(candidate_provider, explicit_or_env_model)
    requested_model = (explicit_model or "").strip()
    env_model = (os.getenv("HARNESS_MODEL") or "").strip()
    requested_from = requested_model or env_model
    if requested_from:
        provider_models = all_providers[candidate_provider].models
        if not _normalize_model(requested_from, provider_models):
            model_source = "fornecido" if requested_model else "variável HARNESS_MODEL"
            warnings.append(
                f"model {model_source} '{requested_from}' inválido para {candidate_provider}; usando '{resolved_model}'"
            )

    cfg = GlobalHarnessConfig(
        default_provider=candidate_provider,
        default_model=resolved_model,
        providers=all_providers,
        workspace_dir=str(merged.get("workspace_dir", ".harness")),
    )

    loaded_model_override = None if explicit_model is None else resolved_model
    loaded = LoadedConfig(
        config=cfg,
        explicit_provider=(candidate_provider if requested_provider == candidate_provider else None),
        explicit_model=loaded_model_override,
        explicit_key=explicit_api_key,
        warnings=warnings,
    )
    return loaded.with_resolved_api_key()


def save_global_config(config: GlobalHarnessConfig, path: Path | None = None) -> None:
    payload = config.as_dict()
    _write_toml(path or GLOBAL_CONFIG, payload)


def save_project_config(workspace: Path, provider: str, model: str | None = None) -> None:
    workspace = Path(workspace)
    provider_name = _normalize_name(provider)
    defaults = normalize_provider_defaults().get(provider_name)
    if not defaults:
        raise ConfigValueError(f"provider desconhecido: {provider_name}")
    payload = {
        "default_provider": provider_name,
        "default_model": model or defaults["default_model"],
    }
    _write_toml(workspace / PROJECT_CONFIG, payload)
