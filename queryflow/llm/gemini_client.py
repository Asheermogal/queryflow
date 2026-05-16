"""Google Gemini provider (google-genai SDK)."""
from __future__ import annotations

from google import genai
from google.genai import types

from llm.base import LLMClient, ModelInfo


_FALLBACK_MODELS = [
    ModelInfo(id="gemini-2.5-pro", display="Gemini 2.5 Pro", context=1_000_000),
    ModelInfo(id="gemini-2.5-flash", display="Gemini 2.5 Flash", context=1_000_000),
    ModelInfo(id="gemini-2.0-flash", display="Gemini 2.0 Flash", context=1_000_000),
]


class GeminiClient(LLMClient):
    provider_id = "google"
    provider_display = "Google"
    models = _FALLBACK_MODELS

    @classmethod
    def list_live_models(cls, api_key: str) -> list[ModelInfo]:
        try:
            client = genai.Client(api_key=api_key)
            data = list(client.models.list())
            out: list[ModelInfo] = []
            for m in data:
                # The new SDK returns Model objects with .name like "models/gemini-2.5-pro"
                name = getattr(m, "name", "") or ""
                mid = name.split("/")[-1] if name else ""
                if not mid.startswith("gemini-"):
                    continue
                # Filter to chat-capable models (skip embedding/imagen)
                if any(skip in mid for skip in ("embed", "imagen", "aqa")):
                    continue
                # Skip deprecated 1.x variants to keep the dropdown clean
                if mid.startswith("gemini-1."):
                    continue
                supported = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", [])
                if supported and "generateContent" not in supported:
                    continue
                out.append(
                    ModelInfo(id=mid, display=cls._humanize(mid), context=1_000_000)
                )
            if not out:
                return _FALLBACK_MODELS
            # Dedupe and sort newest first
            seen: set[str] = set()
            unique: list[ModelInfo] = []
            for m in out:
                if m.id in seen:
                    continue
                seen.add(m.id)
                unique.append(m)
            unique.sort(key=lambda m: m.id, reverse=True)
            return unique
        except Exception:
            return _FALLBACK_MODELS

    @staticmethod
    def _humanize(model_id: str) -> str:
        # gemini-2.5-pro → "Gemini 2.5 Pro"
        parts = model_id.split("-")
        out: list[str] = []
        for p in parts:
            if p[0:1].isdigit():
                out.append(p)
            else:
                out.append(p.capitalize())
        return " ".join(out)

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        client = genai.Client(api_key=self.config.api_key)
        resp = client.models.generate_content(
            model=self.config.model_id,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=0.2,
            ),
        )
        return resp.text or ""
