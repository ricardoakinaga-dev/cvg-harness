"""MiniMax provider using Anthropic-compatible message format."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from cvg_harness.providers.base import Provider, ProviderError, ProviderResponse

try:  # pragma: no cover - integração opcional
    import anthropic  # type: ignore

    _HAS_ANTHROPIC = True
except Exception:  # pragma: no cover - integração opcional
    anthropic = None
    _HAS_ANTHROPIC = False


class MiniMaxProvider(Provider):
    def build_url(self) -> str:
        return f"{self.base_url}/v1/messages"

    def _normalize_messages(
        self,
        prompt: str,
        messages: list[dict[str, Any]] | None,
    ) -> list[dict[str, Any]]:
        if messages:
            normalized = []
            for message in messages:
                content = message.get("content", "")
                normalized.append(
                    {
                        "role": message.get("role", "user"),
                        "content": self._normalize_content(content),
                    }
                )
            return normalized
        return [{"role": "user", "content": self._normalize_content(prompt)}]

    def _normalize_content(self, value: str | Any) -> list[dict[str, str]] | str:
        if isinstance(value, list):
            blocks: list[dict[str, str]] = []
            for item in value:
                if isinstance(item, str):
                    blocks.append({"type": "text", "text": item})
                elif isinstance(item, dict):
                    normalized = dict(item)
                    block_type = str(normalized.get("type", "text"))
                    if block_type == "text":
                        blocks.append(
                            {
                                "type": "text",
                                "text": str(normalized.get("text", normalized.get("content", ""))),
                            }
                        )
                    elif block_type == "tool_result" and isinstance(
                        normalized.get("content"),
                        str,
                    ):
                        blocks.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": str(normalized.get("tool_use_id", "")),
                                "content": str(normalized.get("content", "")),
                            }
                        )
                    else:
                        blocks.append({"type": block_type, "text": str(normalized)})
                else:
                    blocks.append({"type": "text", "text": str(item)})
            return blocks
        if isinstance(value, str):
            return [{"type": "text", "text": value}]
        return [{"type": "text", "text": str(value)}]

    def _normalize_tools(self, tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        normalized: list[dict[str, Any]] = []
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            name = str(tool.get("name", "tool"))
            description = str(tool.get("description", ""))
            schema = tool.get("input_schema") or {}
            if not isinstance(schema, dict):
                schema = {}
            normalized.append(
                {
                    "name": name,
                    "description": description,
                    "input_schema": schema,
                }
            )
        return normalized or None

    def _extract_block_text(self, blocks: Any) -> str:
        if blocks is None:
            return ""
        if isinstance(blocks, (str, bytes)):
            return str(blocks)
        if not isinstance(blocks, Iterable):
            return ""

        parts: list[str] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type", "")).lower()
            if block_type == "text":
                parts.append(str(block.get("text", "")))
            elif block_type == "tool_use":
                tool_name = str(block.get("name", "tool"))
                tool_id = str(block.get("id", ""))
                parts.append(f"[tool_use:{tool_name}:{tool_id}]")
            elif block_type == "tool_result":
                tool_id = str(block.get("tool_use_id", ""))
                content = block.get("content")
                if isinstance(content, str) and content.strip():
                    parts.append(f"[tool_result:{tool_id}:{content}]")
                else:
                    parts.append(f"[tool_result:{tool_id}]")
        return "".join(parts).strip()

    def _extract_anthropic_stream_text(self, event: Any) -> str:
        if event is None:
            return ""

        if hasattr(event, "delta"):
            delta = getattr(event, "delta", None)
            if isinstance(delta, dict):
                text = delta.get("text")
                if text:
                    return str(text)
            if hasattr(delta, "text"):
                text = getattr(delta, "text")
                if text:
                    return str(text)

        if isinstance(event, dict):
            if isinstance(event.get("delta"), dict):
                text = event.get("delta", {}).get("text")
                if text:
                    return str(text)
            content = event.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return self._extract_block_text(content)
            plain = event.get("text")
            if isinstance(plain, str):
                return plain

        if hasattr(event, "content_block"):
            return self._extract_block_text(getattr(event, "content_block", None))
        return ""

    def _safe_serialization(self, payload: Any) -> Any:
        if payload is None:
            return None
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        if hasattr(payload, "to_dict"):
            return payload.to_dict()
        if isinstance(payload, dict):
            return payload
        return str(payload)

    def _to_raw_events(self, events: Iterable[Any]) -> list[Any]:
        dumped: list[Any] = []
        for event in events:
            if hasattr(event, "model_dump"):
                dumped.append(event.model_dump())
            elif hasattr(event, "to_dict"):
                dumped.append(event.to_dict())
            elif isinstance(event, dict):
                dumped.append(event)
            else:
                dumped.append(str(event))
        return dumped

    def _complete_with_anthropic(
        self,
        *,
        prompt: str,
        model: str,
        messages: list[dict[str, Any]] | None,
        tools: list[dict[str, Any]] | None,
        stream: bool = False,
        on_chunk: Callable[[str], None] | None = None,
    ) -> ProviderResponse:
        if not _HAS_ANTHROPIC or anthropic is None:
            raise ProviderError("SDK do Anthropic indisponível.")

        prepared_messages = self._normalize_messages(prompt, messages)
        sdk_tools = self._normalize_tools(tools)
        call_args = {
            "model": model,
            "max_tokens": 2048,
            "messages": prepared_messages,
            "temperature": 0.2,
        }
        if sdk_tools:
            call_args["tools"] = sdk_tools
            call_args["tool_choice"] = {"type": "auto"}

        client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
        if stream:
            call_args["stream"] = True
            chunks: list[Any] = []
            content_parts: list[str] = []
            for event in client.messages.create(**call_args):
                chunks.append(event)
                text = self._extract_anthropic_stream_text(event)
                if text:
                    content_parts.append(text)
                    if callable(on_chunk):
                        on_chunk(text)
            return ProviderResponse(
                model=model,
                content="".join(content_parts).strip(),
                provider=self.name,
                raw={"stream": self._to_raw_events(chunks)},
            )

        response = client.messages.create(**call_args)
        response_text = self._extract_block_text(getattr(response, "content", None))
        return ProviderResponse(
            model=model,
            content=response_text.strip(),
            provider=self.name,
            raw=self._safe_serialization(response),
        )

    def build_payload(
        self,
        prompt: str,
        model: str,
        messages: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        prepared_messages = self._normalize_messages(prompt, messages)
        normalized_tools = self._normalize_tools(tools)
        return {
            "model": model,
            "max_tokens": 2048,
            "messages": prepared_messages,
            "temperature": 0.2,
            "stream": False,
            **({"tools": normalized_tools, "tool_choice": "auto"} if normalized_tools else {}),
        }

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
        resolved_model = self.resolve_model(model)
        if _HAS_ANTHROPIC:
            try:
                return self._complete_with_anthropic(
                    prompt=prompt,
                    model=resolved_model,
                    messages=messages,
                    tools=tools,
                    stream=stream,
                    on_chunk=on_chunk,
                )
            except Exception:
                # fallback robusto para implementação compatível com HTTP
                pass
        return super().complete(
            prompt,
            resolved_model,
            messages=messages,
            tools=tools,
            stream=stream,
            on_chunk=on_chunk,
        )
