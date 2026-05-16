"""Google Gemini provider (using the current google-genai SDK)."""
from __future__ import annotations

from google import genai
from google.genai import types

from llm.base import LLMClient, ModelInfo


class GeminiClient(LLMClient):
    provider_id = "google"
    provider_display = "Google"
    models = [
        ModelInfo(id="gemini-2.5-pro", display="Gemini 2.5 Pro", context=1_000_000),
        ModelInfo(id="gemini-2.5-flash", display="Gemini 2.5 Flash", context=1_000_000),
        ModelInfo(id="gemini-2.0-flash", display="Gemini 2.0 Flash", context=1_000_000),
    ]

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
