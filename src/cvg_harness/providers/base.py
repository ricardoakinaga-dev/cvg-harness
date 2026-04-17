"""Provider abstractions used by the Harness front agent."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


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

    def _extract_response_text(self, payload: dict[str, Any]) -> str:
        message = payload.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                parts: list[str] = []
                for item in content:
                    if not isinstance(item, dict):
                        continue
                    if item.get("type") == "text":
                        parts.append(str(item.get("text", "")))
                        continue
                    if item.get("type") == "tool_use":
                        name = item.get("name", "tool")
                        tool_id = item.get("id", "")
                        parts.append(f"[tool_use:{name}:{tool_id}]")
                    if item.get("type") == "tool_result":
                        tool_result = item.get("content")
                        if isinstance(tool_result, str):
                            parts.append(tool_result)
                        elif isinstance(tool_result, list):
                            for fragment in tool_result:
                                if isinstance(fragment, dict):
                                    parts.append(str(fragment.get("text", "")))
                                    continue
                                parts.append(str(fragment))
                return "".join(parts).strip()
            if isinstance(content, str):
                return content.strip()
        if isinstance(payload, dict) and "results" in payload:
            results = payload.get("results")
            if isinstance(results, list):
                output = []
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    msg = result.get("message")
                    if isinstance(msg, dict):
                        content = msg.get("content")
                        if isinstance(content, str):
                            output.append(content)
                if output:
                    return "\n".join(output).strip()
        return ""

    def normalize_response(self, payload: dict[str, Any], model: str) -> ProviderResponse:
        if "stream" in payload and isinstance(payload["stream"], list):
            return ProviderResponse(
                model=model,
                content=str(payload["stream"]),
                provider=self.name,
                raw=payload,
            )
        text = self._extract_response_text(payload)
        if not text and isinstance(payload.get("choices"), list):
            first = payload["choices"][0]
            if isinstance(first, dict):
                message = first.get("message") or {}
                text = str(message.get("content", ""))
        return ProviderResponse(model=model, content=text.strip(), provider=self.name, raw=payload)

    def complete(
        self,
        prompt: str,
        model: str | None = None,
        *,
        messages: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
        stream: bool = False,
        on_chunk: Callable[[str], None] | None = None,
    ) -> ProviderResponse:
        if not self.api_key:
            raise ProviderError(
                f"Chave de API não configurada para {self.name}. "
                f"Defina {self.api_key_env} no ambiente."
            )
        resolved_model = self.resolve_model(model)
        payload = self.build_payload(
            prompt=prompt,
            model=resolved_model,
            messages=messages,
            tools=tools,
        )
        if stream:
            payload["stream"] = True
            response_payload = self._request(payload, stream=True)
            for chunk in response_payload.get("stream", []):
                if on_chunk:
                    text_chunk = self._extract_text(chunk)
                    if text_chunk:
                        on_chunk(text_chunk)
            return self.normalize_response(response_payload, model=resolved_model)
        response_payload = self._request(payload)
        return self.normalize_response(response_payload, model=resolved_model)

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

    def build_payload(
        self,
        prompt: str,
        model: str,
        messages: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {"prompt": prompt, "model": model}

    def _extract_text(self, chunk: Any) -> str:
        if not isinstance(chunk, dict):
            return ""
        # Anthropic-compatible stream/events.
        if isinstance(chunk.get("delta"), dict):
            delta = chunk["delta"]
            if isinstance(delta, dict) and "text" in delta:
                return str(delta["text"])
            if isinstance(delta, dict) and "content" in delta:
                return str(delta["content"] or "")
        content = chunk.get("content")
        if isinstance(content, list):
            return "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
        if isinstance(content, str):
            return content
        if isinstance(chunk.get("result"), str):
            return str(chunk["result"])
        if isinstance(chunk.get("text"), str):
            return str(chunk["text"])
        return ""

    def _request(
        self,
        payload: dict[str, Any],
        method: str = "POST",
        stream: bool = False,
    ) -> dict[str, Any]:
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
                if stream:
                    events: list[dict[str, Any]] = []
                    for line in raw.splitlines():
                        clean = line.strip()
                        if not clean:
                            continue
                        if clean.startswith("data:"):
                            body = clean[len("data:") :].strip()
                            if body == "[DONE]":
                                continue
                            try:
                                events.append(json.loads(body))
                            except Exception:
                                events.append({"text": body})
                            continue
                        try:
                            events.append(json.loads(clean))
                        except Exception:
                            events.append({"text": clean})
                    return {"stream": events, "raw": raw}
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
