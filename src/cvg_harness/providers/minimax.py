"""MiniMax provider using Anthropic-compatible message format."""

from __future__ import annotations

from cvg_harness.providers.base import Provider


class MiniMaxProvider(Provider):
    def build_url(self) -> str:
        return f"{self.base_url}/v1/messages"

    def build_payload(self, prompt: str, model: str) -> dict:
        return {
            "model": model,
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
        }
