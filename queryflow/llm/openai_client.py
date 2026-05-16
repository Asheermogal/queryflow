"""OpenAI / GPT provider."""
from __future__ import annotations

from openai import OpenAI

from llm.base import LLMClient, ModelInfo


class OpenAIClient(LLMClient):
    provider_id = "openai"
    provider_display = "OpenAI"
    models = [
        ModelInfo(id="gpt-4o", display="GPT-4o", context=128_000),
        ModelInfo(id="gpt-4o-mini", display="GPT-4o mini", context=128_000),
        ModelInfo(id="gpt-4-turbo", display="GPT-4 Turbo", context=128_000),
    ]

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        client = OpenAI(api_key=self.config.api_key)
        resp = client.chat.completions.create(
            model=self.config.model_id,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return resp.choices[0].message.content or ""
