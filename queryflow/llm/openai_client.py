"""OpenAI / GPT provider."""
from __future__ import annotations

from openai import OpenAI

from llm.base import LLMClient, ModelInfo


# Curated fallback list of recent GPT chat models.
# Used if the live API call fails for any reason.
_FALLBACK_MODELS = [
    ModelInfo(id="gpt-4o", display="GPT-4o", context=128_000),
    ModelInfo(id="gpt-4o-mini", display="GPT-4o mini", context=128_000),
    ModelInfo(id="gpt-4-turbo", display="GPT-4 Turbo", context=128_000),
]


class OpenAIClient(LLMClient):
    provider_id = "openai"
    provider_display = "OpenAI"
    models = _FALLBACK_MODELS

    @classmethod
    def list_live_models(cls, api_key: str) -> list[ModelInfo]:
        """Fetch the live list of chat-capable models from the OpenAI API."""
        try:
            client = OpenAI(api_key=api_key)
            data = client.models.list().data
            chat_models: list[ModelInfo] = []
            for m in data:
                mid = m.id
                if not (
                    mid.startswith("gpt-")
                    or mid.startswith("o1")
                    or mid.startswith("o3")
                    or mid.startswith("o4")
                    or mid.startswith("chatgpt-")
                ):
                    continue
                if any(skip in mid for skip in (
                    "audio", "realtime", "transcribe", "tts",
                    "embedding", "image", "moderation", "search", "instruct",
                )):
                    continue
                chat_models.append(
                    ModelInfo(id=mid, display=cls._humanize(mid), context=128_000)
                )
            if not chat_models:
                return _FALLBACK_MODELS
            chat_models.sort(key=lambda m: m.id, reverse=True)
            return chat_models
        except Exception:
            return _FALLBACK_MODELS

    @staticmethod
    def _humanize(model_id: str) -> str:
        parts = model_id.replace("-", " ").split()
        return " ".join(p.upper() if p == "gpt" else p.capitalize() for p in parts)

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
