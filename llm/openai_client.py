"""OpenAI / GPT provider.

Allowed models (hardcoded — no live API call needed):
  - gpt-5.5  : reasoning model; uses max_completion_tokens, no temperature
  - gpt-4o   : standard chat model; uses max_tokens + temperature
"""
from __future__ import annotations

from openai import OpenAI

from llm.base import LLMClient, LLMConfig, ModelInfo


ALLOWED_OPENAI_MODELS: list[ModelInfo] = [
    ModelInfo(id="gpt-5.5", display="GPT 5.5", context=1_000_000),
    ModelInfo(id="gpt-4o",  display="GPT-4o",  context=128_000),
]

# GPT-5.x reasoning models do not accept max_tokens or temperature.
# Detect by prefix or by the literal ".5" version segment.
def _is_gpt5(model_id: str) -> bool:
    return model_id.startswith("gpt-5") or ".5." in model_id or model_id == "gpt-5.5"


class OpenAIClient(LLMClient):
    provider_id = "openai"
    provider_display = "OpenAI"
    models = ALLOWED_OPENAI_MODELS

    @classmethod
    def list_live_models(cls, api_key: str) -> list[ModelInfo]:
        """Return the fixed allowlist. No live API call — avoids exposing
        models whose parameter requirements we haven't vetted."""
        return ALLOWED_OPENAI_MODELS

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        client = OpenAI(api_key=self.config.api_key)
        mid = self.config.model_id

        kwargs: dict = {
            "model": mid,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
        }

        if _is_gpt5(mid):
            # GPT-5.x: max_completion_tokens required; temperature not supported
            kwargs["max_completion_tokens"] = max_tokens
        else:
            # GPT-4o and older: standard params
            kwargs["max_tokens"] = max_tokens
            kwargs["temperature"] = 0.2

        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""
