from __future__ import annotations

from cvg_harness.providers.minimax import MiniMaxProvider


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
