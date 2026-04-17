"""MiniMax provider using Anthropic-compatible message format."""

from __future__ import annotations

from typing import Any

from cvg_harness.providers.base import Provider


class MiniMaxProvider(Provider):
    def build_url(self) -> str:
        return f"{self.base_url}/v1/messages"

    def _normalize_messages(self, prompt: str, messages: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
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
                    elif block_type == "tool_result" and isinstance(normalized.get("content"), str):
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

    def build_payload(
        self,
        prompt: str,
        model: str,
        messages: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        prepared_messages = self._normalize_messages(prompt, messages)
        if tools:
            normalized_tools = []
            for tool in tools:
                if not isinstance(tool, dict):
                    continue
                name = str(tool.get("name", "tool"))
                description = str(tool.get("description", ""))
                schema = tool.get("input_schema") or {}
                if not isinstance(schema, dict):
                    schema = {}
                normalized_tools.append(
                    {
                        "name": name,
                        "description": description,
                        "input_schema": schema,
                    }
                )
        else:
            normalized_tools = None

        return {
            "model": model,
            "max_tokens": 2048,
            "messages": prepared_messages,
            "temperature": 0.2,
            "stream": False,
            **({"tools": normalized_tools, "tool_choice": "auto"} if normalized_tools else {}),
        }
