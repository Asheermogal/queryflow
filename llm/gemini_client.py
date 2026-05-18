"""Google Gemini provider (google-genai SDK >= 1.51).

Allowed model (hardcoded):
  - gemini-3.1-pro-preview : Gemini 3.1 Pro; supports temperature (0-2.0)
                             and max_output_tokens (max 65,536).

ThinkingLevel.LOW is set explicitly so the model returns instantly without
deep chain-of-thought reasoning, as required for a responsive analytics app.
"""
from __future__ import annotations

from google import genai
from google.genai import types

from llm.base import LLMClient, ModelInfo


ALLOWED_GEMINI_MODELS: list[ModelInfo] = [
    ModelInfo(id="gemini-3.1-pro-preview", display="Gemini 3.1 Pro", context=1_000_000),
]


class GeminiClient(LLMClient):
    provider_id = "google"
    provider_display = "Google"
    models = ALLOWED_GEMINI_MODELS

    @classmethod
    def list_live_models(cls, api_key: str) -> list[ModelInfo]:
        """Return the fixed allowlist. No live API call needed."""
        return ALLOWED_GEMINI_MODELS

    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        client = genai.Client(api_key=self.config.api_key)
        resp = client.models.generate_content(
            model=self.config.model_id,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=min(max_tokens, 65_536),  # model hard cap
                temperature=0.2,
                thinking_config=types.ThinkingConfig(
                    thinking_level=types.ThinkingLevel.LOW,
                ),
            ),
        )
        return resp.text or ""
