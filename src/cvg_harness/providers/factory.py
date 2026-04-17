"""Factory to instantiate provider adapters."""

from __future__ import annotations

from typing import Callable

from cvg_harness.config import ConfigValueError, LoadedConfig, ProviderConfig
from cvg_harness.providers.base import Provider
from cvg_harness.providers.minimax import MiniMaxProvider
from cvg_harness.providers.openai import OpenAIProvider
from cvg_harness.providers.openrouter import OpenRouterProvider


ProviderFactory = Callable[[ProviderConfig, str | None], Provider]


def _build_minimax(cfg, api_key: str | None) -> Provider:
    return MiniMaxProvider(
        name="minimax",
        base_url=cfg.base_url,
        api_key=api_key,
        api_key_env=cfg.api_key_env,
        models=cfg.models,
        default_model=cfg.default_model,
    )


def _build_openai(cfg, api_key: str | None) -> Provider:
    return OpenAIProvider(
        name="openai",
        base_url=cfg.base_url,
        api_key=api_key,
        api_key_env=cfg.api_key_env,
        models=cfg.models,
        default_model=cfg.default_model,
    )


def _build_openrouter(cfg, api_key: str | None) -> Provider:
    return OpenRouterProvider(
        name="openrouter",
        base_url=cfg.base_url,
        api_key=api_key,
        api_key_env=cfg.api_key_env,
        models=cfg.models,
        default_model=cfg.default_model,
    )


PROVIDERS: dict[str, ProviderFactory] = {
    "minimax": _build_minimax,
    "openai": _build_openai,
    "openrouter": _build_openrouter,
}


def build_provider(config: LoadedConfig) -> Provider:
    cfg = config.provider_cfg()
    provider_id = config.provider
    builder = PROVIDERS.get(provider_id)
    if not builder:
        raise ConfigValueError(f"provider desconhecido: {provider_id}")
    return builder(cfg, config.explicit_key)
