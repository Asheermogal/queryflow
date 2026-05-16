"""OpenAI / GPT provider.

Key fixes:
- o1/o3/o4 reasoning models require `max_completion_tokens` not `max_tokens`
- o1/o3/o4 do not support the `temperature` parameter
- Model display names cleaned up (strips date suffixes)
"""
from __future__ import annotations

from openai import OpenAI

from llm.base import LLMClient, ModelInfo


_FALLBACK_MODELS = [
    ModelInfo(id="gpt-4o", display="GPT-4o", context=128_000),
    ModelInfo(id="gpt-4o-mini", display="GPT-4o mini", context=128_000),
    ModelInfo(id="o4-mini", display="o4-mini", context=128_000),
]

# Models that use max_completion_tokens and don't support temperature
_REASONING_PREFIXES = ("o1", "o3", "o4")


def _is_reasoning_model(model_id: str) -> bool:
    return any(model_id.startswith(p) for p in _REASONING_PREFIXES)


def _humanize(model_id: str) -> str:
    import re
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
                    "dalle", "whisper",
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
            deduped = sorted(seen_display.values(), key=lambda m: m.id, reverse=True)
            return deduped
        except Exception:
            return _FALLBACK_MODELS

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        client = OpenAI(api_key=self.config.api_key)
        if _is_reasoning_model(self.config.model_id):
            resp = client.chat.completions.create(
                model=self.config.model_id,
                messages=[{"role": "user", "content": f"{system}\n\n{user}"}],
                max_completion_tokens=max_tokens,
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
