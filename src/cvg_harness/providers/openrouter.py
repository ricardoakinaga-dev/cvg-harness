"""OpenRouter provider (compatível com API de chat)."""

from __future__ import annotations

from cvg_harness.providers.base import Provider


class OpenRouterProvider(Provider):
    def build_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def build_payload(self, prompt: str, model: str) -> dict:
        return {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "provider": {
                "order": ["openrouter"]
            },
            "max_tokens": 1024,
            "temperature": 0.2,
        }
