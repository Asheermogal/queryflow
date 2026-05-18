"""Anthropic / Claude provider.

Allowed models (hardcoded):
  - claude-opus-4-7   : most capable; temperature silently ignored by API — omit it
  - claude-sonnet-4-6 : fast + intelligent; temperature supported normally
"""
from __future__ import annotations

from anthropic import Anthropic

from llm.base import LLMClient, ModelInfo


ALLOWED_ANTHROPIC_MODELS: list[ModelInfo] = [
    ModelInfo(id="claude-opus-4-7",   display="Claude Opus 4.7",   context=1_000_000),
    ModelInfo(id="claude-sonnet-4-6", display="Claude Sonnet 4.6", context=1_000_000),
]

# Opus 4.7 drops sampling parameters entirely; temperature is silently ignored.
# Omit it cleanly so the code matches the API contract and is future-proof.
_NO_TEMPERATURE_MODELS = {"claude-opus-4-7"}


class AnthropicClient(LLMClient):
    provider_id = "anthropic"
    provider_display = "Anthropic"
    models = ALLOWED_ANTHROPIC_MODELS

    @classmethod
    def list_live_models(cls, api_key: str) -> list[ModelInfo]:
        """Return the fixed allowlist. No live API call needed."""
        return ALLOWED_ANTHROPIC_MODELS

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        client = Anthropic(api_key=self.config.api_key)
        mid = self.config.model_id

        kwargs: dict = {
            "model":      mid,
            "max_tokens": max_tokens,
            "system":     system,
            "messages":   [{"role": "user", "content": user}],
        }

        if mid not in _NO_TEMPERATURE_MODELS:
            kwargs["temperature"] = 0.2

        resp = client.messages.create(**kwargs)
        return "".join(b.text for b in resp.content if b.type == "text")
