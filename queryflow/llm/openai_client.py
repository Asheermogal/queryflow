"""OpenAI / GPT provider.

Key behaviors:
- Detects o-series reasoning models (o1, o3, o4) and uses max_completion_tokens
  instead of max_tokens, drops temperature, and applies a 6x token multiplier
  to leave room for the model's internal reasoning tokens.
- Sorts the live model list so standard chat models (gpt-4o, gpt-4o-mini)
  come BEFORE reasoning models, so the default selection is a fast/cheap
  chat model rather than a slow reasoning model.
"""
from __future__ import annotations

import re

from openai import OpenAI

from llm.base import LLMClient, ModelInfo


_FALLBACK_MODELS = [
    ModelInfo(id="gpt-4o-mini", display="GPT-4o mini", context=128_000),
    ModelInfo(id="gpt-4o", display="GPT-4o", context=128_000),
    ModelInfo(id="o4-mini", display="o4-mini", context=128_000),
]

_REASONING_PREFIXES = ("o1", "o3", "o4")
_REASONING_TOKEN_MULTIPLIER = 6


def _is_reasoning_model(model_id: str) -> bool:
    return any(model_id.startswith(p) for p in _REASONING_PREFIXES)


def _humanize(model_id: str) -> str:
    cleaned = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", model_id)
    if re.match(r"^o\d", cleaned):
        return cleaned
    parts = cleaned.split("-")
    out = ""
    for p in parts:
        if p.lower() in ("gpt", "chatgpt"):
            out = p.upper()
        elif p and p[0].isdigit():
            out = out + "-" + p
        else:
            out = out + " " + p.capitalize()
    return out.strip()


def _model_priority(model_id: str) -> tuple[int, str]:
    if _is_reasoning_model(model_id):
        return (5, model_id)
    if model_id.startswith("gpt-4o-mini"):
        return (0, model_id)
    if model_id.startswith("gpt-4o"):
        return (1, model_id)
    if model_id.startswith("gpt-4"):
        return (2, model_id)
    if model_id.startswith("gpt-"):
        return (3, model_id)
    if model_id.startswith("chatgpt-"):
        return (4, model_id)
    return (6, model_id)


class OpenAIClient(LLMClient):
    provider_id = "openai"
    provider_display = "OpenAI"
    models = _FALLBACK_MODELS

    @classmethod
    def list_live_models(cls, api_key: str) -> list[ModelInfo]:
        try:
            client = OpenAI(api_key=api_key)
            data = client.models.list().data
            chat_models: list[ModelInfo] = []
            for m in data:
                mid = m.id
                is_gpt = mid.startswith("gpt-") or mid.startswith("chatgpt-")
                is_o = any(mid.startswith(p) for p in _REASONING_PREFIXES)
                if not (is_gpt or is_o):
                    continue
                if any(skip in mid for skip in (
                    "audio", "realtime", "transcribe", "tts",
                    "embedding", "image", "moderation", "search", "instruct",
                    "dalle", "whisper", "preview",
                )):
                    continue
                chat_models.append(
                    ModelInfo(id=mid, display=_humanize(mid), context=128_000)
                )
            if not chat_models:
                return _FALLBACK_MODELS

            chat_models.sort(key=lambda m: m.id, reverse=True)
            seen_display: dict[str, ModelInfo] = {}
            for m in chat_models:
                if m.display not in seen_display:
                    seen_display[m.display] = m
            deduped = list(seen_display.values())
            deduped.sort(key=lambda m: _model_priority(m.id))
            return deduped
        except Exception:
            return _FALLBACK_MODELS

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        client = OpenAI(api_key=self.config.api_key)

        if _is_reasoning_model(self.config.model_id):
            budget = max(max_tokens * _REASONING_TOKEN_MULTIPLIER, 4000)
            resp = client.chat.completions.create(
                model=self.config.model_id,
                messages=[{"role": "user", "content": f"{system}\n\n{user}"}],
                max_completion_tokens=budget,
            )
        else:
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
