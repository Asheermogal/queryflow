"""Anthropic / Claude provider."""
from __future__ import annotations

from anthropic import Anthropic

from llm.base import LLMClient, ModelInfo


class AnthropicClient(LLMClient):
    provider_id = "anthropic"
    provider_display = "Anthropic"
    models = [
        ModelInfo(id="claude-sonnet-4-5", display="Claude Sonnet 4.5", context=200_000),
        ModelInfo(id="claude-opus-4-1", display="Claude Opus 4.1", context=200_000),
        ModelInfo(id="claude-haiku-4-5", display="Claude Haiku 4.5", context=200_000),
    ]

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        client = Anthropic(api_key=self.config.api_key)
        resp = client.messages.create(
            model=self.config.model_id,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=0.2,
        )
        return "".join(b.text for b in resp.content if b.type == "text")
