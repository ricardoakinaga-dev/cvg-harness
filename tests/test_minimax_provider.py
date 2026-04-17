from __future__ import annotations

from cvg_harness.providers.minimax import MiniMaxProvider
from cvg_harness.providers import minimax as minimax_module
from cvg_harness.providers.base import ProviderResponse


def test_minimax_provider_builds_anthropic_payload_with_tools() -> None:
    provider = MiniMaxProvider(
        name="minimax",
        base_url="https://api.minimax.io/anthropic",
        api_key="x",
        api_key_env="ANTHROPIC_API_KEY",
        models=["MiniMax-M2.7", "MiniMax-M2.7-highspeed"],
        default_model="MiniMax-M2.7",
    )

    payload = provider.build_payload(
        prompt="Crie uma função de login.",
        model="MiniMax-M2.7",
        messages=[{"role": "user", "content": "Crie uma função de login."}],
        tools=[
            {
                "name": "filesystem_read",
                "description": "Lê arquivo",
                "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
            }
        ],
    )

    assert payload["model"] == "MiniMax-M2.7"
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][0]["content"][0]["type"] == "text"
    assert payload["tools"][0]["name"] == "filesystem_read"
    assert payload["tool_choice"] == "auto"
    assert payload["stream"] is False
    assert payload["max_tokens"] >= 512


def test_minimax_provider_complete_extracts_text(monkeypatch) -> None:
    provider = MiniMaxProvider(
        name="minimax",
        base_url="https://api.minimax.io/anthropic",
        api_key="x",
        api_key_env="ANTHROPIC_API_KEY",
        models=["MiniMax-M2.7", "MiniMax-M2.7-highspeed"],
        default_model="MiniMax-M2.7",
    )

    def _fake_request(payload, method="POST", stream=False):  # type: ignore[override]
        assert payload["model"] == "MiniMax-M2.7"
        return {"message": {"content": [{"type": "text", "text": "ok"}]}}

    monkeypatch.setattr(provider, "_request", _fake_request)
    response = provider.complete("texto", model="MiniMax-M2.7")
    assert response.content == "ok"
    assert response.provider == "minimax"


def test_minimax_provider_prefers_anthropic_sdk_when_available(monkeypatch) -> None:
    monkeypatch.setattr(minimax_module, "_HAS_ANTHROPIC", True)

    provider = MiniMaxProvider(
        name="minimax",
        base_url="https://api.minimax.io/anthropic",
        api_key="x",
        api_key_env="ANTHROPIC_API_KEY",
        models=["MiniMax-M2.7", "MiniMax-M2.7-highspeed"],
        default_model="MiniMax-M2.7",
    )
    called = {"count": 0}

    def _sdk_complete(*args, **kwargs) -> ProviderResponse:
        called["count"] += 1
        assert kwargs["model"] == "MiniMax-M2.7"
        return ProviderResponse(
            model="MiniMax-M2.7",
            content="via sdk",
            provider="minimax",
            raw={"mode": "sdk"},
        )

    monkeypatch.setattr(provider, "_complete_with_anthropic", _sdk_complete)

    response = provider.complete("texto", model="MiniMax-M2.7", stream=True, on_chunk=lambda chunk: None)
    assert called["count"] == 1
    assert response.content == "via sdk"
    assert response.provider == "minimax"
