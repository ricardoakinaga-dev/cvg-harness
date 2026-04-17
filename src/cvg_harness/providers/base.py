"""Provider abstractions used by the Harness front agent."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class ProviderError(RuntimeError):
    """Erro de integração com provider."""


@dataclass
class ProviderResponse:
    model: str
    content: str
    provider: str
    raw: dict[str, Any]


class Provider:
    name: str = "base"
    base_url: str
    api_key_env: str
    default_model: str
    models: list[str]

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str | None,
        api_key_env: str,
        models: list[str],
        default_model: str,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or ""
        self.api_key_env = api_key_env
        self.models = models
        self.default_model = default_model

    def supports(self, model: str) -> bool:
        return model in self.models

    def resolve_model(self, model: str | None) -> str:
        if model and self.supports(model):
            return model
        return self.default_model

    def normalize_response(self, payload: dict[str, Any], model: str) -> ProviderResponse:
        text = ""
        if isinstance(payload, dict):
            message = payload.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, list):
                    text = "".join(item.get("text", "") for item in content if isinstance(item, dict))
                elif isinstance(content, str):
                    text = content
            if not text and isinstance(payload.get("choices"), list):
                first = payload["choices"][0]
                if isinstance(first, dict):
                    message = first.get("message") or {}
                    text = str(message.get("content", ""))
        return ProviderResponse(model=model, content=text.strip(), provider=self.name, raw=payload)

    def complete(self, prompt: str, model: str | None = None) -> ProviderResponse:
        if not self.api_key:
            raise ProviderError(
                f"Chave de API não configurada para {self.name}. "
                f"Defina {self.api_key_env} no ambiente."
            )
        payload = self.build_payload(prompt=prompt, model=self.resolve_model(model))
        response_payload = self._request(payload)
        return self.normalize_response(response_payload, model=self.resolve_model(model))

    def test_connection(self) -> bool:
        # Conexão mínima válida para onboarding.
        if not self.api_key:
            return False
        try:
            self._request(self.build_payload("ping", model=self.default_model), method="POST")
            return True
        except Exception:
            # O objetivo do check é experiência de setup; não bloquear execução.
            return False

    def _request(self, payload: dict[str, Any], method: str = "POST") -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        request = urllib.request.Request(
            url=self.build_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                return json.loads(raw or "{}")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise ProviderError(f"{self.name}: {exc.code} {exc.reason} {body[:200]}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"{self.name}: {exc.reason}") from exc
        except Exception as exc:
            raise ProviderError(f"{self.name}: erro inesperado {exc}") from exc

    def build_url(self) -> str:
        return self.base_url

    def build_payload(self, prompt: str, model: str) -> dict[str, Any]:
        return {"prompt": prompt, "model": model}
