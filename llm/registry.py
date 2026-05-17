"""
Provider registry — knows which providers exist, auto-detects which one
to use based on the API key configured in Streamlit secrets, and fetches
the live model list from that provider.
"""
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

# Maps provider_id → secrets.toml key
SECRETS_KEYS: dict[str, str] = {
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "google": "google_api_key",
}


def provider_display(provider_id: str) -> str:
    return PROVIDERS[provider_id].provider_display


def detect_provider_from_secrets(secrets) -> tuple[str | None, str | None]:
    """Inspect the secrets object and return (provider_id, api_key) for whichever
    provider has a key configured. Priority: openai > anthropic > google.
    Returns (None, None) if no key is configured or no secrets file exists.
    """
    for provider_id in PROVIDERS.keys():
        key_name = SECRETS_KEYS[provider_id]
        try:
            value = secrets.get(key_name, "") if hasattr(secrets, "get") else ""
        except Exception:
            return None, None
        if value and value.strip():
            return provider_id, value.strip()
    return None, None


def fetch_live_models(provider_id: str, api_key: str) -> list[ModelInfo]:
    """Pull the current model list from the provider's API.
    Falls back to the client's curated list if the call fails.
    """
    cls = PROVIDERS[provider_id]
    return cls.list_live_models(api_key)


def build_client(config: LLMConfig) -> LLMClient:
    cls = PROVIDERS[config.provider_id]
    return cls(config)


def model_display(provider_id: str, model_id: str, models: list[ModelInfo] | None = None) -> str:
    """Resolve provider+model to a human-readable label."""
    pool = models if models is not None else PROVIDERS[provider_id].models
    for m in pool:
        if m.id == model_id:
            return m.display
    return model_id
