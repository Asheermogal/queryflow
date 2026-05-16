"""Abstract LLM client. Each provider implements `complete`."""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModelInfo:
    """A model offered by a provider."""
    id: str           # API identifier (e.g., "gpt-4o")
    display: str      # UI label (e.g., "GPT-4o")
    context: int      # Approximate context window (tokens)


@dataclass
class LLMConfig:
    provider_id: str
    model_id: str
    api_key: str


class LLMClient(ABC):
    """One per provider. Stateless — config is passed at construction time."""

    provider_id: str = ""
    provider_display: str = ""
    models: list[ModelInfo] = []

    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
        """Return the raw text completion."""

    def complete_json(self, system: str, user: str, max_tokens: int = 1500) -> dict[str, Any]:
        """Run completion and parse the result as JSON.

        Strips markdown code fences and extracts the first balanced JSON object.
        Raises ValueError if no JSON found or parsing fails.
        """
        text = self.complete(system, user, max_tokens=max_tokens)
        return extract_json(text)


# ── JSON extraction utility ──────────────────────────────────────────────
def extract_json(text: str) -> dict[str, Any]:
    """Pull the first JSON object out of an LLM response. Tolerates fenced output."""
    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model response: {text[:200]}")
    return json.loads(cleaned[start : end + 1])
