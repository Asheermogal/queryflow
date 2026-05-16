"""Anthropic / Claude provider."""
from __future__ import annotations

from anthropic import Anthropic

from llm.base import LLMClient, ModelInfo


# Curated fallback — current Claude lineup as of May 2026.
_FALLBACK_MODELS = [
    ModelInfo(id="claude-opus-4-7", display="Claude Opus 4.7", context=200_000),
    ModelInfo(id="claude-opus-4-6", display="Claude Opus 4.6", context=200_000),
    ModelInfo(id="claude-sonnet-4-6", display="Claude Sonnet 4.6", context=200_000),
    ModelInfo(id="claude-haiku-4-5", display="Claude Haiku 4.5", context=200_000),
]


class AnthropicClient(LLMClient):
    provider_id = "anthropic"
    provider_display = "Anthropic"
    models = _FALLBACK_MODELS

    @classmethod
    def list_live_models(cls, api_key: str) -> list[ModelInfo]:
        """Fetch live model list from Anthropic. Falls back to curated list."""
        try:
            client = Anthropic(api_key=api_key)
            data = client.models.list().data
            out: list[ModelInfo] = []
            for m in data:
                mid = m.id
                if not mid.startswith("claude-"):
                    continue
                out.append(
                    ModelInfo(id=mid, display=cls._humanize(mid), context=200_000)
                )
            if not out:
                return _FALLBACK_MODELS
            # Sort newest first — Anthropic's id naming sorts well with reverse
            out.sort(key=lambda m: m.id, reverse=True)
            return out
        except Exception:
            return _FALLBACK_MODELS

    @staticmethod
    def _humanize(model_id: str) -> str:
        # claude-opus-4-7 → "Claude Opus 4.7"
        parts = model_id.split("-")
        # Group trailing version digits like "4-7" or "4-5-20251022" → "4.7"
        out_parts: list[str] = []
        version_buf: list[str] = []
        for p in parts:
            if p.isdigit():
                version_buf.append(p)
            else:
                if version_buf:
                    out_parts.append(".".join(version_buf))
                    version_buf = []
                out_parts.append(p.capitalize())
        if version_buf:
            # Keep only the first 2 numeric components for the version (4.7)
            # drop date suffixes
            out_parts.append(".".join(version_buf[:2]))
        return " ".join(out_parts)

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
