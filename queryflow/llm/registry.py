"""Provider registry. The UI talks to this; new providers just register here."""
from __future__ import annotations

from llm.anthropic_client import AnthropicClient
from llm.base import LLMClient, LLMConfig, ModelInfo
from llm.gemini_client import GeminiClient
from llm.openai_client import OpenAIClient

PROVIDERS: dict[str, type[LLMClient]] = {
    OpenAIClient.provider_id: OpenAIClient,
    AnthropicClient.provider_id: AnthropicClient,
    GeminiClient.provider_id: GeminiClient,
}


def provider_options() -> list[tuple[str, str]]:
    """[(provider_id, display_name), ...] in stable display order."""
    return [(cls.provider_id, cls.provider_display) for cls in PROVIDERS.values()]


def models_for(provider_id: str) -> list[ModelInfo]:
    return PROVIDERS[provider_id].models


def secrets_key_for(provider_id: str) -> str:
    """Map provider → secrets.toml key for optional pre-baked keys."""
    return {
        "openai": "openai_api_key",
        "anthropic": "anthropic_api_key",
        "google": "google_api_key",
    }[provider_id]


def build_client(config: LLMConfig) -> LLMClient:
    cls = PROVIDERS[config.provider_id]
    return cls(config)


def model_display(provider_id: str, model_id: str) -> str:
    """Resolve provider+model to a user-facing label."""
    for m in models_for(provider_id):
        if m.id == model_id:
            return m.display
    return model_id
