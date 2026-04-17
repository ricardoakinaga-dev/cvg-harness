"""OpenAI-compatible provider."""

from __future__ import annotations

from cvg_harness.providers.base import Provider


class OpenAIProvider(Provider):
    def build_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    def build_payload(self, prompt: str, model: str) -> dict:
        return {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Você é o assistente do Harness, objetivo e técnico."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }
